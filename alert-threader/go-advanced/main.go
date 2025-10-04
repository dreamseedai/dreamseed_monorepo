package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/redis/go-redis/v9"
)

// 환경 변수
var (
	slackBotToken = mustEnv("SLACK_BOT_TOKEN")
	slackChannel  = mustEnv("SLACK_CHANNEL")
	environment   = getEnv("ENVIRONMENT", "staging")
	bindHost      = getEnv("BIND_HOST", "0.0.0.0")
	bindPort      = getEnv("BIND_PORT", "9009")

	// 저장소 설정
	threadStore     = getEnv("THREAD_STORE", "file")
	threadStoreFile = getEnv("THREAD_STORE_FILE", "/var/lib/alert-threader/threads.json")
	redisURL        = getEnv("REDIS_URL", "redis://localhost:6379/0")
	redisKeyPrefix  = getEnv("REDIS_KEY_PREFIX", "threader:ts")

	// 전역 변수
	threadCache = make(map[string]string) // key -> thread_ts
	cacheMutex  = sync.RWMutex{}
	redisClient *redis.Client
	ctx         = context.Background()
)

// 유틸리티 함수
func mustEnv(key string) string {
	value := os.Getenv(key)
	if value == "" {
		log.Fatalf("❌ %s 환경 변수가 필요합니다", key)
	}
	return value
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getSeverityColor(severity string) string {
	colorMap := map[string]string{
		"critical": "#E01E5A", // 빨강
		"warning":  "#ECB22E", // 노랑
		"info":     "#2EB67D", // 초록
		"error":    "#E01E5A", // 빨강
		"success":  "#2EB67D", // 초록
		"debug":    "#36C5F0", // 파랑
	}
	if color, exists := colorMap[strings.ToLower(severity)]; exists {
		return color
	}
	return "#2EB67D"
}

func getSeverityEmoji(severity string) string {
	emojiMap := map[string]string{
		"critical": "🚨",
		"warning":  "⚠️",
		"info":     "ℹ️",
		"error":    "❌",
		"success":  "✅",
		"debug":    "🐛",
	}
	if emoji, exists := emojiMap[strings.ToLower(severity)]; exists {
		return emoji
	}
	return "📢"
}

func threadKey(labels map[string]string) string {
	name := labels["alertname"]
	if name == "" {
		name = "unknown"
	}
	severity := labels["severity"]
	if severity == "" {
		severity = "info"
	}
	service := labels["service"]
	if service == "" {
		service = "unknown"
	}
	cluster := labels["cluster"]
	if cluster == "" {
		cluster = "default"
	}
	return fmt.Sprintf("%s|%s|%s|%s|%s", name, severity, service, cluster, environment)
}

func formatTimestamp(timestamp string) string {
	if timestamp == "" {
		return ""
	}
	
	t, err := time.Parse(time.RFC3339, timestamp)
	if err != nil {
		return timestamp
	}
	return t.Format("2006-01-02 15:04:05 UTC")
}

// 저장소 관리 (파일/Redis)
func ensureParentDirectory(filePath string) {
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		log.Printf("디렉터리 생성 실패: %v", err)
	}
}

func loadCacheFile() {
	if threadStore != "file" {
		return
	}
	
	data, err := os.ReadFile(threadStoreFile)
	if err != nil {
		if !os.IsNotExist(err) {
			log.Printf("파일 캐시 로드 실패: %v", err)
		}
		return
	}
	
	if err := json.Unmarshal(data, &threadCache); err != nil {
		log.Printf("파일 캐시 파싱 실패: %v", err)
		return
	}
	
	log.Printf("📁 파일에서 %d개 스레드 로드됨", len(threadCache))
}

func saveCacheFile() {
	if threadStore != "file" {
		return
	}
	
	ensureParentDirectory(threadStoreFile)
	tmpFile := threadStoreFile + ".tmp"
	
	data, err := json.MarshalIndent(threadCache, "", "  ")
	if err != nil {
		log.Printf("파일 캐시 마샬링 실패: %v", err)
		return
	}
	
	if err := os.WriteFile(tmpFile, data, 0644); err != nil {
		log.Printf("파일 캐시 저장 실패: %v", err)
		return
	}
	
	if err := os.Rename(tmpFile, threadStoreFile); err != nil {
		log.Printf("파일 캐시 이동 실패: %v", err)
		return
	}
	
	log.Printf("💾 파일에 %d개 스레드 저장됨", len(threadCache))
}

func loadCacheRedis() error {
	if threadStore != "redis" {
		return nil
	}
	
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return fmt.Errorf("Redis URL 파싱 실패: %v", err)
	}
	
	redisClient = redis.NewClient(opt)
	
	// 연결 테스트
	if err := redisClient.Ping(ctx).Err(); err != nil {
		return fmt.Errorf("Redis 연결 실패: %v", err)
	}
	
	log.Println("🔴 Redis 연결 초기화됨")
	return nil
}

func storeGetTs(key string) (string, error) {
	cacheMutex.RLock()
	ts := threadCache[key]
	cacheMutex.RUnlock()
	
	if ts != "" {
		return ts, nil
	}
	
	if threadStore == "redis" && redisClient != nil {
		ts, err := redisClient.Get(ctx, redisKeyPrefix+":"+key).Result()
		if err != nil {
			if err == redis.Nil {
				return "", nil
			}
			return "", fmt.Errorf("Redis 조회 실패: %v", err)
		}
		
		if ts != "" {
			cacheMutex.Lock()
			threadCache[key] = ts
			cacheMutex.Unlock()
		}
		return ts, nil
	}
	
	return "", nil
}

func storeSetTs(key, ts string) error {
	cacheMutex.Lock()
	threadCache[key] = ts
	cacheMutex.Unlock()
	
	if threadStore == "redis" && redisClient != nil {
		if err := redisClient.Set(ctx, redisKeyPrefix+":"+key, ts, 0).Err(); err != nil {
			return fmt.Errorf("Redis 저장 실패: %v", err)
		}
		log.Printf("🔴 Redis에 스레드 저장: %s -> %s", key, ts)
		return nil
	}
	
	saveCacheFile()
	return nil
}

// Slack Block Kit 포맷팅
func buildAlertBlocks(alert Alert, status string) []interface{} {
	labels := alert.Labels
	annotations := alert.Annotations
	
	alertname := labels["alertname"]
	if alertname == "" {
		alertname = "Unknown"
	}
	severity := labels["severity"]
	if severity == "" {
		severity = "info"
	}
	service := labels["service"]
	if service == "" {
		service = "unknown"
	}
	instance := labels["instance"]
	cluster := labels["cluster"]
	if cluster == "" {
		cluster = "default"
	}
	
	summary := annotations["summary"]
	if summary == "" {
		summary = alertname
	}
	description := annotations["description"]
	runbookURL := annotations["runbook_url"]
	
	emoji := getSeverityEmoji(severity)
	
	// 상태에 따른 헤더 텍스트
	var headerText string
	if status == "resolved" {
		headerText = fmt.Sprintf("✅ RESOLVED — %s", summary)
	} else {
		headerText = fmt.Sprintf("%s %s", emoji, summary)
	}
	
	// 헤더 블록
	blocks := []interface{}{
		map[string]interface{}{
			"type": "header",
			"text": map[string]interface{}{
				"type":  "plain_text",
				"text":  headerText,
				"emoji": true,
			},
		},
	}
	
	// 필드 섹션
	fields := []interface{}{
		map[string]interface{}{
			"type": "mrkdwn",
			"text": fmt.Sprintf("*Severity:*\n`%s`", strings.ToUpper(severity)),
		},
		map[string]interface{}{
			"type": "mrkdwn",
			"text": fmt.Sprintf("*Environment:*\n`%s`", environment),
		},
		map[string]interface{}{
			"type": "mrkdwn",
			"text": fmt.Sprintf("*Service:*\n`%s`", service),
		},
		map[string]interface{}{
			"type": "mrkdwn",
			"text": fmt.Sprintf("*Cluster:*\n`%s`", cluster),
		},
	}
	
	// 인스턴스가 있으면 추가
	if instance != "" {
		fields = append(fields, map[string]interface{}{
			"type": "mrkdwn",
			"text": fmt.Sprintf("*Instance:*\n`%s`", instance),
		})
	}
	
	blocks = append(blocks, map[string]interface{}{
		"type":   "section",
		"fields": fields,
	})
	
	// 설명이 있으면 추가
	if description != "" {
		blocks = append(blocks, map[string]interface{}{
			"type": "section",
			"text": map[string]interface{}{
				"type": "mrkdwn",
				"text": fmt.Sprintf("*Description:*\n%s", description),
			},
		})
	}
	
	// Runbook URL이 있으면 추가
	if runbookURL != "" {
		blocks = append(blocks, map[string]interface{}{
			"type": "section",
			"text": map[string]interface{}{
				"type": "mrkdwn",
				"text": fmt.Sprintf("*Runbook:* <%s|View Runbook>", runbookURL),
			},
		})
	}
	
	// 시간 정보
	startsAt := alert.StartsAt
	endsAt := alert.EndsAt
	
	var timeInfo []string
	if startsAt != "" {
		timeInfo = append(timeInfo, fmt.Sprintf("Started: %s", formatTimestamp(startsAt)))
	}
	if endsAt != "" && status == "resolved" {
		timeInfo = append(timeInfo, fmt.Sprintf("Resolved: %s", formatTimestamp(endsAt)))
	}
	
	if len(timeInfo) > 0 {
		blocks = append(blocks, map[string]interface{}{
			"type": "context",
			"elements": []interface{}{
				map[string]interface{}{
					"type": "mrkdwn",
					"text": strings.Join(timeInfo, " | "),
				},
			},
		})
	}
	
	// 환경 정보
	blocks = append(blocks, map[string]interface{}{
		"type": "context",
		"elements": []interface{}{
			map[string]interface{}{
				"type": "mrkdwn",
				"text": fmt.Sprintf("`env=%s` | `alertname=%s`", environment, alertname),
			},
		},
	})
	
	return blocks
}

func buildAlertAttachments(alert Alert, status string) []interface{} {
	labels := alert.Labels
	severity := labels["severity"]
	if severity == "" {
		severity = "info"
	}
	color := getSeverityColor(severity)
	
	// 기본 attachment
	attachment := map[string]interface{}{
		"color":    color,
		"fallback": fmt.Sprintf("[%s] %s", environment, labels["alertname"]),
	}
	
	// 필드 구성
	var fields []map[string]interface{}
	
	// 심각도
	fields = append(fields, map[string]interface{}{
		"title": "Severity",
		"value": strings.ToUpper(severity),
		"short": true,
	})
	
	// 환경
	fields = append(fields, map[string]interface{}{
		"title": "Environment",
		"value": environment,
		"short": true,
	})
	
	// 서비스
	if service := labels["service"]; service != "" {
		fields = append(fields, map[string]interface{}{
			"title": "Service",
			"value": service,
			"short": true,
		})
	}
	
	// 클러스터
	if cluster := labels["cluster"]; cluster != "" {
		fields = append(fields, map[string]interface{}{
			"title": "Cluster",
			"value": cluster,
			"short": true,
		})
	}
	
	// 인스턴스
	if instance := labels["instance"]; instance != "" {
		fields = append(fields, map[string]interface{}{
			"title": "Instance",
			"value": instance,
			"short": true,
		})
	}
	
	// Job
	if job := labels["job"]; job != "" {
		fields = append(fields, map[string]interface{}{
			"title": "Job",
			"value": job,
			"short": true,
		})
	}
	
	attachment["fields"] = fields
	
	// 설명
	if description := alert.Annotations["description"]; description != "" {
		attachment["text"] = description
	}
	
	// 시간 정보
	if startsAt := alert.StartsAt; startsAt != "" {
		if t, err := time.Parse(time.RFC3339, startsAt); err == nil {
			attachment["ts"] = t.Unix()
		}
	}
	
	return []interface{}{attachment}
}

func slackPostMessage(text string, blocks []interface{}, attachments []interface{}, threadTs string) (string, error) {
	payload := map[string]interface{}{
		"channel":       slackChannel,
		"text":          text,
		"unfurl_links":  false,
		"unfurl_media":  false,
	}
	
	if len(blocks) > 0 {
		payload["blocks"] = blocks
	}
	if len(attachments) > 0 {
		payload["attachments"] = attachments
	}
	if threadTs != "" {
		payload["thread_ts"] = threadTs
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("JSON 마샬링 실패: %v", err)
	}
	
	req, err := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", bytes.NewReader(jsonData))
	if err != nil {
		return "", fmt.Errorf("HTTP 요청 생성 실패: %v", err)
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+slackBotToken)
	
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("HTTP 요청 실패: %v", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("응답 읽기 실패: %v", err)
	}
	
	var slackResp struct {
		OK    bool   `json:"ok"`
		TS    string `json:"ts"`
		Error string `json:"error"`
	}
	
	if err := json.Unmarshal(body, &slackResp); err != nil {
		return "", fmt.Errorf("응답 파싱 실패: %v", err)
	}
	
	if !slackResp.OK {
		return "", fmt.Errorf("Slack API 오류: %s", slackResp.Error)
	}
	
	return slackResp.TS, nil
}

// 데이터 구조체
type AlertWebhook struct {
	Status   string  `json:"status"`
	GroupKey string  `json:"groupKey"`
	Alerts   []Alert `json:"alerts"`
}

type Alert struct {
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	StartsAt    string            `json:"startsAt"`
	EndsAt      string            `json:"endsAt"`
}

type APIResponse struct {
	OK      bool          `json:"ok"`
	Count   int           `json:"count"`
	Status  string        `json:"status,omitempty"`
	Results []AlertResult `json:"results,omitempty"`
	Error   string        `json:"error,omitempty"`
}

type AlertResult struct {
	Key       string `json:"key"`
	ThreadTS  string `json:"thread_ts"`
	Status    string `json:"status"`
	Alertname string `json:"alertname"`
	Severity  string `json:"severity"`
	Error     string `json:"error,omitempty"`
}

// HTTP 핸들러
func healthHandler(w http.ResponseWriter, r *http.Request) {
	cacheMutex.RLock()
	cacheSize := len(threadCache)
	cacheMutex.RUnlock()
	
	healthData := map[string]interface{}{
		"status":         "healthy",
		"environment":    environment,
		"channel":        slackChannel,
		"thread_store":   threadStore,
		"cached_threads": cacheSize,
		"timestamp":      time.Now().Format(time.RFC3339),
	}
	
	// Redis 연결 상태 확인
	if threadStore == "redis" && redisClient != nil {
		if err := redisClient.Ping(ctx).Err(); err != nil {
			healthData["redis_status"] = fmt.Sprintf("error: %v", err)
		} else {
			healthData["redis_status"] = "connected"
		}
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(healthData)
}

func alertHandler(w http.ResponseWriter, r *http.Request) {
	var webhook AlertWebhook
	if err := json.NewDecoder(r.Body).Decode(&webhook); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	
	log.Printf("📨 Received %d alerts with status: %s", len(webhook.Alerts), webhook.Status)
	
	var results []AlertResult
	
	for _, alert := range webhook.Alerts {
		key := threadKey(alert.Labels)
		
		threadTs, err := storeGetTs(key)
		if err != nil {
			log.Printf("스레드 조회 실패: %v", err)
			results = append(results, AlertResult{
				Key:   key,
				Error: err.Error(),
			})
			continue
		}
		
		labels := alert.Labels
		annotations := alert.Annotations
		
		alertname := labels["alertname"]
		if alertname == "" {
			alertname = "Unknown"
		}
		severity := labels["severity"]
		if severity == "" {
			severity = "info"
		}
		summary := annotations["summary"]
		if summary == "" {
			summary = alertname
		}
		
		// 메시지 텍스트 (fallback)
		var text string
		if webhook.Status == "resolved" {
			text = fmt.Sprintf("[%s] ✅ RESOLVED: %s", environment, summary)
		} else {
			text = fmt.Sprintf("[%s] %s: %s", environment, strings.ToUpper(severity), summary)
		}
		
		// Block Kit 구성
		blocks := buildAlertBlocks(alert, webhook.Status)
		
		// Attachments 구성
		attachments := buildAlertAttachments(alert, webhook.Status)
		
		// 스레드가 없으면 새 메시지 생성
		if threadTs == "" {
			ts, err := slackPostMessage(text, blocks, attachments, "")
			if err != nil {
				log.Printf("Slack 메시지 전송 실패: %v", err)
				results = append(results, AlertResult{
					Key:   key,
					Error: err.Error(),
				})
				continue
			}
			threadTs = ts
			
			if err := storeSetTs(key, threadTs); err != nil {
				log.Printf("스레드 저장 실패: %v", err)
			}
			
			log.Printf("🧵 새 스레드 생성: %s -> %s", key, threadTs)
		} else {
			// 기존 스레드에 답글
			_, err := slackPostMessage(text, blocks, attachments, threadTs)
			if err != nil {
				log.Printf("Slack 답글 전송 실패: %v", err)
				results = append(results, AlertResult{
					Key:   key,
					Error: err.Error(),
				})
				continue
			}
			
			log.Printf("💬 스레드 답글: %s -> %s", key, threadTs)
		}
		
		results = append(results, AlertResult{
			Key:       key,
			ThreadTS:  threadTs,
			Status:    webhook.Status,
			Alertname: alertname,
			Severity:  severity,
		})
	}
	
	response := APIResponse{
		OK:      true,
		Count:   len(results),
		Status:  webhook.Status,
		Results: results,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func cacheHandler(w http.ResponseWriter, r *http.Request) {
	cacheMutex.RLock()
	defer cacheMutex.RUnlock()
	
	threads := make(map[string]string)
	for k, v := range threadCache {
		threads[k] = v
	}
	
	response := map[string]interface{}{
		"cached_threads": len(threadCache),
		"threads":        threads,
		"thread_store":   threadStore,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func clearCacheHandler(w http.ResponseWriter, r *http.Request) {
	cacheMutex.Lock()
	defer cacheMutex.Unlock()
	
	threadCache = make(map[string]string)
	
	// Redis에서도 삭제
	if threadStore == "redis" && redisClient != nil {
		keys, err := redisClient.Keys(ctx, redisKeyPrefix+":*").Result()
		if err == nil && len(keys) > 0 {
			redisClient.Del(ctx, keys...)
		}
	}
	
	response := map[string]string{
		"message": "캐시가 초기화되었습니다",
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	stats := map[string]interface{}{
		"cached_threads": len(threadCache),
		"thread_store":   threadStore,
		"environment":    environment,
		"uptime":         time.Now().Format(time.RFC3339),
	}
	
	if threadStore == "redis" && redisClient != nil {
		info, err := redisClient.Info(ctx, "server").Result()
		if err == nil {
			// 간단한 파싱 (실제로는 더 정교한 파싱 필요)
			lines := strings.Split(info, "\n")
			redisStats := make(map[string]string)
			for _, line := range lines {
				if strings.Contains(line, ":") && !strings.HasPrefix(line, "#") {
					parts := strings.SplitN(line, ":", 2)
					if len(parts) == 2 {
						redisStats[parts[0]] = strings.TrimSpace(parts[1])
					}
				}
			}
			stats["redis"] = redisStats
		} else {
			stats["redis_error"] = err.Error()
		}
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func main() {
	log.Println("🚀 DreamSeed Alert Threader - Advanced (Go) 시작 중...")
	
	// 저장소 초기화
	if threadStore == "redis" {
		if err := loadCacheRedis(); err != nil {
			log.Fatalf("Redis 초기화 실패: %v", err)
		}
	} else {
		loadCacheFile()
	}
	
	log.Printf("저장소: %s", threadStore)
	log.Printf("환경: %s", environment)
	log.Printf("채널: %s", slackChannel)
	
	// 라우터 설정
	r := mux.NewRouter()
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/alert", alertHandler).Methods("POST")
	r.HandleFunc("/cache", cacheHandler).Methods("GET")
	r.HandleFunc("/cache", clearCacheHandler).Methods("DELETE")
	r.HandleFunc("/stats", statsHandler).Methods("GET")
	
	// 서버 시작
	port, _ := strconv.Atoi(bindPort)
	addr := fmt.Sprintf("%s:%d", bindHost, port)
	
	log.Printf("🌐 서버 시작됨: http://%s", addr)
	log.Printf("엔드포인트: POST /alert, GET /health, GET /stats")
	
	log.Fatal(http.ListenAndServe(addr, r))
}

