package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

var (
	slackToken = mustEnv("SLACK_BOT_TOKEN")
	slackCh    = mustEnv("SLACK_CHANNEL") // channel ID 권장
	envName    = getenv("ENVIRONMENT", "staging")

	storeKind  = getenv("THREAD_STORE", "file") // file | redis
	storeFile  = getenv("THREAD_STORE_FILE", "/var/lib/alert-threader/threads.json")
	redisURL   = getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
	redisPref  = getenv("REDIS_KEY_PREFIX", "threader:ts")
	redisTimeout = getenv("REDIS_TIMEOUT", "5")

	mem   = map[string]string{} // key -> ts (always used as local cache)
	mu    sync.RWMutex
	rdb   *redis.Client // go-redis client
	startupTime = time.Now()
)

func mustEnv(k string) string {
	v := os.Getenv(k)
	if v == "" { log.Fatalf("%s required", k) }
	return v
}
func getenv(k, d string) string { if v:=os.Getenv(k); v!=""; return v; return d }

func ensureParent(p string) {
	_ = os.MkdirAll(filepath.Dir(p), 0o755)
}
func loadFile() {
	b, err := os.ReadFile(storeFile)
	if err == nil {
		_ = json.Unmarshal(b, &mem)
	} else if !errors.Is(err, os.ErrNotExist) {
		log.Printf("Error loading file cache: %v", err)
	}
}
func saveFile() {
	if storeKind != "file" { return }
	ensureParent(storeFile)
	tmp := storeFile + ".tmp"
	if err := os.WriteFile(tmp, mustJSON(mem), 0o644); err != nil {
		log.Printf("Error writing temporary cache file: %v", err)
		return
	}
	if err := os.Rename(tmp, storeFile); err != nil {
		log.Printf("Error renaming temporary cache file: %v", err)
	}
}
func mustJSON(v any) []byte {
	b, err := json.Marshal(v)
	if err != nil { log.Fatalf("Failed to marshal JSON: %v", err) }
	return b
}

func threadKey(lbl map[string]string) string {
	name := lbl["alertname"]; if name == "" { name = "unknown" }
	sev  := lbl["severity"];  if sev == ""  { sev = "info" }
	// Add more labels for finer-grained threading if needed
	// e.g., cluster := lbl["cluster"]; if cluster == "" { cluster = "default" }
	// return name + "|" + sev + "|" + envName + "|" + cluster
	return name + "|" + sev + "|" + envName
}
func sevColor(sev string) string {
	switch sev {
	case "critical": return "#E01E5A"
	case "warning":  return "#ECB22E"
	default:         return "#2EB67D"
	}
}
func sevEmoji(sev string) string {
	switch sev {
	case "critical": return "🚨"
	case "warning":  return "⚠️"
	default:         return "ℹ️"
	}
}

func buildBlocks(summary, sev, desc string, labels map[string]string) []any {
	fields := []any{
		map[string]any{"type":"mrkdwn","text":"*Severity:*\n`"+sev+"`"},
		map[string]any{"type":"mrkdwn","text":"*Environment:*\n`"+envName+"`"},
	}
	for _, k := range []string{"alertname","instance","job","service","cluster"} {
		if v, ok := labels[k]; ok && v != "" {
			fields = append(fields, map[string]any{"type":"mrkdwn","text":"*"+k+":*\n`"+v+"`"})
		}
	}
	blocks := []any{
		map[string]any{"type":"header","text":map[string]any{"type":"plain_text","text":sevEmoji(sev)+" "+summary,"emoji":true}},
		map[string]any{"type":"section","fields":fields},
	}
	if desc != "" {
		blocks = append(blocks, map[string]any{"type":"section","text":map[string]any{"type":"mrkdwn","text":desc}})
	}
	blocks = append(blocks, map[string]any{"type":"context","elements":[]any{map[string]any{"type":"mrkdwn","text":"`env="+envName+"`"}}})
	return blocks
}

func slackPost(text string, blocks []any, threadTS, color string) (string, error) {
	payload := map[string]any{"channel": slackCh, "text": text, "unfurl_links": false, "unfurl_media": false}
	if len(blocks) > 0 { payload["blocks"] = blocks }
	if threadTS != "" { payload["thread_ts"] = threadTS }
	if color != ""   { payload["attachments"] = []any{ map[string]any{"color": color} } }

	b, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", bytes.NewReader(b))
	req.Header.Set("Content-Type","application/json")
	req.Header.Set("Authorization","Bearer "+slackToken)

	resp, err := http.DefaultClient.Do(req)
	if err != nil { return "", fmt.Errorf("failed to send slack request: %w", err) }
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("slack API returned non-OK status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var out struct{ OK bool `json:"ok"`; TS string `json:"ts"`; Error string `json:"error"` }
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", fmt.Errorf("failed to decode slack response: %w", err)
	}
	if !out.OK { return "", errors.New("slack: "+out.Error) }
	return out.TS, nil
}

func storeGet(key string) (string, error) {
	mu.RLock(); ts := mem[key]; mu.RUnlock()
	if ts != "" { return ts, nil } // Local cache hit

	if storeKind == "redis" && rdb != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		v, err := rdb.Get(ctx, redisPref+":"+key).Result()
		if err == nil && v != "" {
			mu.Lock(); mem[key] = v; mu.Unlock() // Update local cache
			return v, nil
		}
		if err != nil && !errors.Is(err, redis.Nil) {
			log.Printf("Redis GET error for key %s: %v", key, err)
		}
	}
	return "", nil
}
func storeSet(key, ts string) error {
	mu.Lock(); mem[key] = ts; mu.Unlock() // Update local cache

	if storeKind == "redis" && rdb != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := rdb.Set(ctx, redisPref+":"+key, ts, 0).Err(); err != nil { // 0 for no expiration
			log.Printf("Redis SET error for key %s: %v", key, err)
			return err
		}
		return nil
	}
	saveFile()
	return nil
}

type alertReq struct {
	Status string `json:"status"`
	Alerts []struct{
		Labels map[string]string `json:"labels"`
		Annotations map[string]string `json:"annotations"`
		StartsAt time.Time `json:"startsAt"`
		EndsAt *time.Time `json:"endsAt,omitempty"`
	} `json:"alerts"`
}

func alertHandler(w http.ResponseWriter, r *http.Request) {
	var in alertReq
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		http.Error(w, fmt.Sprintf("invalid request body: %v", err), http.StatusBadRequest); return
	}
	for _, a := range in.Alerts {
		key := threadKey(a.Labels)
		ts, _ := storeGet(key)

		sev := a.Labels["severity"]; if sev=="" { sev="info" }
		sum := a.Annotations["summary"]; if sum=="" { sum = a.Labels["alertname"] }
		desc:= a.Annotations["description"]

		title := sum
		text  := fmt.Sprintf("[%s] %s — %s", envName, sev, sum)
		if in.Status == "resolved" {
			title = "RESOLVED — " + sum
			text  = fmt.Sprintf("[%s] ✅ RESOLVED: %s", envName, sum)
		}
		blocks := buildBlocks(title, sev, desc, a.Labels)
		color  := sevColor(sev)

		var err error
		if ts == "" {
			ts, err = slackPost(text, blocks, "", color)
		} else {
			_, err = slackPost(text, blocks, ts, color)
		}
		if err != nil {
			log.Printf("slack error for alert %s: %v", sum, err)
			continue
		}
		if err := storeSet(key, ts); err != nil {
			log.Printf("store set error for alert %s: %v", sum, err)
		}
	}
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"ok":true}`))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	resp := map[string]any{
		"status": "healthy",
		"environment": envName,
		"channel": slackCh,
		"thread_store": storeKind,
		"cached_threads": len(mem),
		"timestamp": time.Now().Format(time.RFC3339),
	}

	if storeKind == "redis" && rdb != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		_, err := rdb.Ping(ctx).Result()
		if err != nil {
			resp["redis_status"] = fmt.Sprintf("disconnected: %v", err)
			resp["status"] = "degraded"
		} else {
			resp["redis_status"] = "connected"
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	resp := map[string]any{
		"cached_threads": len(mem),
		"thread_store": storeKind,
		"environment": envName,
		"uptime": time.Since(startupTime).String(),
		"startup_time": startupTime.Format(time.RFC3339),
	}

	if storeKind == "redis" && rdb != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		info, err := rdb.Info(ctx, "memory", "clients", "keyspace").Result()
		if err != nil {
			resp["redis_info_error"] = err.Error()
		} else {
			resp["redis_info"] = info
		}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func cacheHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodDelete {
		mu.Lock()
		mem = make(map[string]string) // Clear local cache
		mu.Unlock()

		if storeKind == "file" {
			if err := os.Remove(storeFile); err != nil && !errors.Is(err, os.ErrNotExist) {
				log.Printf("Error deleting cache file: %v", err)
				http.Error(w, fmt.Sprintf("Error deleting cache file: %v", err), http.StatusInternalServerError)
				return
			}
		} else if storeKind == "redis" && rdb != nil {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			// This will delete all keys with the prefix. Be careful in production.
			iter := rdb.Scan(ctx, 0, redisPref+":*", 0).Iterator()
			for iter.Next(ctx) {
				if err := rdb.Del(ctx, iter.Val()).Err(); err != nil {
					log.Printf("Error deleting Redis key %s: %v", iter.Val(), err)
				}
			}
			if err := iter.Err(); err != nil {
				log.Printf("Error iterating Redis keys: %v", err)
				http.Error(w, fmt.Sprintf("Error clearing Redis cache: %v", err), http.StatusInternalServerError)
				return
			}
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"ok":true, "message":"Cache cleared"}`))
		return
	}

	// GET /cache
	mu.RLock()
	defer mu.RUnlock()
	resp := map[string]any{
		"thread_store": storeKind,
		"cached_threads_count": len(mem),
		"cached_threads": mem,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func main() {
	if storeKind == "file" {
		loadFile()
		log.Println("File storage selected. Loaded cache from", storeFile)
	} else if storeKind == "redis" {
		opt, err := redis.ParseURL(redisURL)
		if err != nil { 
			log.Fatalf("Failed to parse Redis URL %s: %v", redisURL, err) 
		}
		rdb = redis.NewClient(opt)
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_, err = rdb.Ping(ctx).Result()
		if err != nil {
			log.Fatalf("Failed to connect to Redis at %s: %v", redisURL, err)
		}
		log.Println("Redis storage selected. Connected to Redis at", redisURL)
	}

	http.HandleFunc("/alert", alertHandler)
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/stats", statsHandler)
	http.HandleFunc("/cache", cacheHandler) // GET and DELETE
	addr := ":9009"
	log.Println("threader listening on", addr, "(store="+storeKind+")")
	log.Fatal(http.ListenAndServe(addr, nil))
}

