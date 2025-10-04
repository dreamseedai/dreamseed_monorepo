package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

// =============================
// Environment Variables
// =============================
var (
	slackBotToken   = os.Getenv("SLACK_BOT_TOKEN")
	slackChannel    = os.Getenv("SLACK_CHANNEL")  // 권장: 채널 ID(Cxxxx)
	environment     = getEnv("ENVIRONMENT", "staging")
	threadStore     = getEnv("THREAD_STORE", "file")   // file|redis
	threadStoreFile = getEnv("THREAD_STORE_FILE", "/var/lib/alert-threader/threads.json")
	redisURL        = getEnv("REDIS_URL", "redis://localhost:6379/0")
	redisKeyPrefix  = getEnv("REDIS_KEY_PREFIX", "threader:ts")
)

// =============================
// Application
// =============================
var (
	_threadCache = make(map[string]string) // key -> thread_ts
	_redis       *redis.Client
	_mu          sync.RWMutex
	_rctx        = context.Background()
)

// =============================
// Utilities
// =============================
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func sevColor(sev string) string {
	sev = strings.ToLower(sev)
	switch sev {
	case "critical":
		return "#E01E5A"
	case "warning":
		return "#ECB22E"
	default:
		return "#2EB67D"
	}
}

func sevEmoji(sev string) string {
	switch strings.ToLower(sev) {
	case "critical":
		return "🚨"
	case "warning":
		return "⚠️"
	default:
		return "ℹ️"
	}
}

func threadKey(alert map[string]interface{}) string {
	labels, _ := alert["labels"].(map[string]interface{})
	name, _ := labels["alertname"].(string)
	sev, _ := labels["severity"].(string)
	if name == "" {
		name = "unknown"
	}
	if sev == "" {
		sev = "info"
	}
	return fmt.Sprintf("%s|%s|%s", name, sev, environment)
}

// =============================
// Storage (File / Redis)
// =============================
func loadCacheFile() {
	_mu.Lock()
	defer _mu.Unlock()
	
	if _, err := os.Stat(threadStoreFile); os.IsNotExist(err) {
		_threadCache = make(map[string]string)
		return
	}
	
	data, err := ioutil.ReadFile(threadStoreFile)
	if err != nil {
		log.Printf("Failed to load cache file: %v", err)
		_threadCache = make(map[string]string)
		return
	}
	
	if err := json.Unmarshal(data, &_threadCache); err != nil {
		log.Printf("Failed to parse cache file: %v", err)
		_threadCache = make(map[string]string)
	}
}

func saveCacheFile() {
	if threadStore != "file" {
		return
	}
	
	_mu.RLock()
	data, err := json.Marshal(_threadCache)
	_mu.RUnlock()
	
	if err != nil {
		log.Printf("Failed to marshal cache: %v", err)
		return
	}
	
	dir := filepath.Dir(threadStoreFile)
	if err := os.MkdirAll(dir, 0755); err != nil {
		log.Printf("Failed to create cache directory: %v", err)
		return
	}
	
	tmp := threadStoreFile + ".tmp"
	if err := ioutil.WriteFile(tmp, data, 0644); err != nil {
		log.Printf("Failed to write cache file: %v", err)
		return
	}
	
	if err := os.Rename(tmp, threadStoreFile); err != nil {
		log.Printf("Failed to rename cache file: %v", err)
	}
}

func loadCacheRedis() error {
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return fmt.Errorf("redis parse: %v", err)
	}
	
	_redis = redis.NewClient(opt)
	if err := _redis.Ping(_rctx).Err(); err != nil {
		return fmt.Errorf("redis ping: %v", err)
	}
	
	_mu.Lock()
	_threadCache = make(map[string]string)
	_mu.Unlock()
	
	return nil
}

func storeGetTS(key string) (string, error) {
	_mu.RLock()
	ts := _threadCache[key]
	_mu.RUnlock()
	
	if ts != "" {
		return ts, nil
	}
	
	if threadStore == "redis" && _redis != nil {
		v, err := _redis.Get(_rctx, fmt.Sprintf("%s:%s", redisKeyPrefix, key)).Result()
		if err == redis.Nil {
			return "", nil
		}
		if err != nil {
			return "", err
		}
		if v != "" {
			_mu.Lock()
			_threadCache[key] = v
			_mu.Unlock()
		}
		return v, nil
	}
	
	return "", nil
}

func storeSetTS(key, ts string) error {
	_mu.Lock()
	_threadCache[key] = ts
	_mu.Unlock()
	
	if threadStore == "redis" && _redis != nil {
		if err := _redis.Set(_rctx, fmt.Sprintf("%s:%s", redisKeyPrefix, key), ts, 0).Err(); err != nil {
			return err
		}
		return nil
	}
	
	saveCacheFile()
	return nil
}

// =============================
// Slack payload (Block Kit + attachments color)
// =============================
func buildBlocks(summary, sev, description string, labels map[string]interface{}) []map[string]interface{} {
	emoji := sevEmoji(sev)
	fields := []map[string]interface{}{
		{"type": "mrkdwn", "text": fmt.Sprintf("*Severity:*\n`%s`", sev)},
		{"type": "mrkdwn", "text": fmt.Sprintf("*Environment:*\n`%s`", environment)},
	}
	
	for _, k := range []string{"alertname", "instance", "job"} {
		if v, ok := labels[k].(string); ok && v != "" {
			fields = append(fields, map[string]interface{}{
				"type": "mrkdwn", 
				"text": fmt.Sprintf("*%s:*\n`%s`", k, v),
			})
		}
	}
	
	blocks := []map[string]interface{}{
		{
			"type": "header",
			"text": map[string]interface{}{
				"type": "plain_text",
				"text": fmt.Sprintf("%s %s", emoji, summary),
				"emoji": true,
			},
		},
		{
			"type": "section",
			"fields": fields,
		},
	}
	
	if description != "" {
		blocks = append(blocks, map[string]interface{}{
			"type": "section",
			"text": map[string]interface{}{
				"type": "mrkdwn",
				"text": description,
			},
		})
	}
	
	blocks = append(blocks, map[string]interface{}{
		"type": "context",
		"elements": []map[string]interface{}{
			{
				"type": "mrkdwn",
				"text": fmt.Sprintf("`env=%s`", environment),
			},
		},
	})
	
	return blocks
}

func slackPostMessage(text string, blocks []map[string]interface{}, threadTS string, color string) (map[string]interface{}, error) {
	payload := map[string]interface{}{
		"channel":       slackChannel,
		"text":          text,
		"unfurl_links":  false,
		"unfurl_media":  false,
	}
	
	if blocks != nil {
		payload["blocks"] = blocks
	}
	if threadTS != "" {
		payload["thread_ts"] = threadTS
	}
	if color != "" {
		payload["attachments"] = []map[string]interface{}{
			{"color": color},
		}
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}
	
	req, err := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", strings.NewReader(string(jsonData)))
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", slackBotToken))
	req.Header.Set("Content-Type", "application/json")
	
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}
	
	if ok, _ := result["ok"].(bool); !ok {
		return nil, fmt.Errorf("slack error: %v", result)
	}
	
	return result, nil
}

// =============================
// HTTP Handlers
// =============================
func alertHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	var body map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	
	status, _ := body["status"].(string)
	alerts, _ := body["alerts"].([]interface{})
	
	var results []map[string]interface{}
	
	for _, alertInterface := range alerts {
		alert, _ := alertInterface.(map[string]interface{})
		labels, _ := alert["labels"].(map[string]interface{})
		ann, _ := alert["annotations"].(map[string]interface{})
		
		key := threadKey(alert)
		ts, _ := storeGetTS(key)
		
		summary, _ := ann["summary"].(string)
		if summary == "" {
			summary, _ = labels["alertname"].(string)
		}
		if summary == "" {
			summary = "(no summary)"
		}
		
		description, _ := ann["description"].(string)
		sev, _ := labels["severity"].(string)
		if sev == "" {
			sev = "info"
		}
		color := sevColor(sev)
		
		var text string
		var blocks []map[string]interface{}
		
		if status == "resolved" {
			text = fmt.Sprintf("[%s] ✅ RESOLVED: %s", environment, summary)
			blocks = buildBlocks(fmt.Sprintf("RESOLVED — %s", summary), sev, description, labels)
		} else {
			text = fmt.Sprintf("[%s] %s — %s", environment, strings.ToUpper(sev), summary)
			blocks = buildBlocks(summary, sev, description, labels)
		}
		
		if ts == "" {
			data, err := slackPostMessage(text, blocks, "", color)
			if err != nil {
				log.Printf("Failed to post message: %v", err)
				continue
			}
			newTS, _ := data["ts"].(string)
			storeSetTS(key, newTS)
			results = append(results, map[string]interface{}{
				"key": key, "thread_ts": newTS, "status": status,
			})
		} else {
			if err := slackPostMessage(text, blocks, ts, color); err != nil {
				log.Printf("Failed to post message: %v", err)
				continue
			}
			results = append(results, map[string]interface{}{
				"key": key, "thread_ts": ts, "status": status,
			})
		}
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"ok": true, "count": len(results), "results": results,
	})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "ok", "store": threadStore, "env": environment,
	})
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	_mu.RLock()
	cacheSize := len(_threadCache)
	_mu.RUnlock()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"thread_cache_size": cacheSize,
		"store_type":        threadStore,
		"environment":       environment,
	})
}

// =============================
// Main
// =============================
func main() {
	log.Println("Starting Alert Threader (Go)...")
	
	// Initialize storage
	if threadStore == "redis" {
		if err := loadCacheRedis(); err != nil {
			log.Fatalf("Redis initialization failed: %v", err)
		}
		log.Printf("Redis connected: %s", redisURL)
	} else {
		loadCacheFile()
		log.Printf("File storage initialized: %s", threadStoreFile)
	}
	
	// Setup HTTP routes
	http.HandleFunc("/alert", alertHandler)
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/stats", statsHandler)
	
	// Start server
	port := getEnv("PORT", "9011")
	host := getEnv("HOST", "0.0.0.0")
	addr := fmt.Sprintf("%s:%s", host, port)
	
	log.Printf("Alert Threader (Go) listening on %s", addr)
	log.Printf("Environment: %s", environment)
	log.Printf("Store: %s", threadStore)
	
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
