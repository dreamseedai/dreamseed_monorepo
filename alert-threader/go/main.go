package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/mux"
)

// 환경 변수
var (
	slackBotToken = os.Getenv("SLACK_BOT_TOKEN")
	slackChannel  = os.Getenv("SLACK_CHANNEL")
	environment   = getEnv("ENVIRONMENT", "staging")
	bindHost      = getEnv("BIND_HOST", "0.0.0.0")
	bindPort      = getEnv("BIND_PORT", "9009")
)

// 스레드 캐시 (실제 운영에서는 Redis나 파일 저장 권장)
var (
	threadCache = make(map[string]string)
	cacheMutex  = sync.RWMutex{}
)

// Alertmanager webhook 구조체
type AlertWebhook struct {
	Status   string  `json:"status"`
	GroupKey string  `json:"groupKey"`
	Alerts   []Alert `json:"alerts"`
}

type Alert struct {
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	StartsAt    time.Time         `json:"startsAt"`
	EndsAt      time.Time         `json:"endsAt"`
}

// Slack API 응답 구조체
type SlackResponse struct {
	OK    bool   `json:"ok"`
	TS    string `json:"ts"`
	Error string `json:"error"`
}

// Slack 메시지 구조체
type SlackMessage struct {
	Channel     string        `json:"channel"`
	Text        string        `json:"text"`
	ThreadTS    string        `json:"thread_ts,omitempty"`
	UnfurlLinks bool          `json:"unfurl_links"`
	UnfurlMedia bool          `json:"unfurl_media"`
	Blocks      []interface{} `json:"blocks,omitempty"`
}

// API 응답 구조체
type APIResponse struct {
	OK      bool        `json:"ok"`
	Count   int         `json:"count"`
	Status  string      `json:"status,omitempty"`
	Results []AlertResult `json:"results,omitempty"`
	Error   string      `json:"error,omitempty"`
}

type AlertResult struct {
	Key      string `json:"key"`
	ThreadTS string `json:"thread_ts"`
	Status   string `json:"status"`
	Alertname string `json:"alertname"`
	Error    string `json:"error,omitempty"`
}

// 유틸리티 함수
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func threadKey(alert Alert) string {
	name := alert.Labels["alertname"]
	if name == "" {
		name = "unknown"
	}
	severity := alert.Labels["severity"]
	if severity == "" {
		severity = "info"
	}
	service := alert.Labels["service"]
	if service == "" {
		service = "unknown"
	}
	return fmt.Sprintf("%s|%s|%s|%s", name, severity, service, environment)
}

func getEmoji(severity string) string {
	emojiMap := map[string]string{
		"critical": "🚨",
		"warning":  "⚠️",
		"info":     "ℹ️",
		"error":    "❌",
		"success":  "✅",
	}
	if emoji, exists := emojiMap[strings.ToLower(severity)]; exists {
		return emoji
	}
	return "📢"
}

func getColor(severity string) string {
	colorMap := map[string]string{
		"critical": "#E01E5A",
		"warning":  "#ECB22E",
		"info":     "#2EB67D",
		"error":    "#E01E5A",
		"success":  "#2EB67D",
	}
	if color, exists := colorMap[strings.ToLower(severity)]; exists {
		return color
	}
	return "#2EB67D"
}

func formatAlertMessage(alert Alert, status string) (string, []interface{}) {
	alertname := alert.Labels["alertname"]
	if alertname == "" {
		alertname = "Unknown"
	}
	severity := alert.Labels["severity"]
	if severity == "" {
		severity = "info"
	}
	summary := alert.Annotations["summary"]
	if summary == "" {
		summary = alertname
	}
	description := alert.Annotations["description"]

	emoji := getEmoji(severity)

	// 상태에 따른 메시지 포맷
	var text string
	if status == "resolved" {
		text = fmt.Sprintf("*[%s]* ✅ **RESOLVED** - %s", environment, summary)
	} else {
		text = fmt.Sprintf("*[%s]* %s **%s** (`%s`)", environment, emoji, summary, severity)
	}

	// Slack Block Kit 포맷
	blocks := []interface{}{
		map[string]interface{}{
			"type": "section",
			"text": map[string]interface{}{
				"type": "mrkdwn",
				"text": text,
			},
		},
	}

	if description != "" {
		blocks = append(blocks, map[string]interface{}{
			"type": "section",
			"text": map[string]interface{}{
				"type": "mrkdwn",
				"text": fmt.Sprintf("*설명:* %s", description),
			},
		})
	}

	// 라벨 정보
	labelKeys := []string{"alertname", "severity", "service", "instance"}
	var labelParts []string
	for _, key := range labelKeys {
		if value, exists := alert.Labels[key]; exists {
			labelParts = append(labelParts, fmt.Sprintf("`%s=%s`", key, value))
		}
	}

	if len(labelParts) > 0 {
		blocks = append(blocks, map[string]interface{}{
			"type": "context",
			"elements": []interface{}{
				map[string]interface{}{
					"type": "mrkdwn",
					"text": fmt.Sprintf("*라벨:* %s", strings.Join(labelParts, " | ")),
				},
			},
		})
	}

	return text, blocks
}

func postSlack(text string, threadTS string, blocks []interface{}) (*SlackResponse, error) {
	message := SlackMessage{
		Channel:     slackChannel,
		Text:        text,
		UnfurlLinks: false,
		UnfurlMedia: false,
	}

	if threadTS != "" {
		message.ThreadTS = threadTS
	}

	if blocks != nil {
		message.Blocks = blocks
	}

	jsonData, err := json.Marshal(message)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+slackBotToken)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var slackResp SlackResponse
	if err := json.NewDecoder(resp.Body).Decode(&slackResp); err != nil {
		return nil, err
	}

	if !slackResp.OK {
		return nil, fmt.Errorf("Slack API 오류: %s", slackResp.Error)
	}

	return &slackResp, nil
}

// HTTP 핸들러
func healthHandler(w http.ResponseWriter, r *http.Request) {
	cacheMutex.RLock()
	cacheSize := len(threadCache)
	cacheMutex.RUnlock()

	response := map[string]interface{}{
		"status":         "healthy",
		"environment":    environment,
		"channel":        slackChannel,
		"cached_threads": cacheSize,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
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
		key := threadKey(alert)
		
		cacheMutex.RLock()
		threadTS := threadCache[key]
		cacheMutex.RUnlock()

		text, blocks := formatAlertMessage(alert, webhook.Status)

		var err error
		if threadTS == "" {
			// 새 스레드 생성
			resp, err := postSlack(text, "", blocks)
			if err != nil {
				log.Printf("❌ Slack API 오류: %v", err)
				results = append(results, AlertResult{
					Key:   key,
					Error: err.Error(),
				})
				continue
			}
			threadTS = resp.TS
			
			cacheMutex.Lock()
			threadCache[key] = threadTS
			cacheMutex.Unlock()
			
			log.Printf("🧵 새 스레드 생성: %s -> %s", key, threadTS)
		} else {
			// 기존 스레드에 답글
			_, err = postSlack(text, threadTS, blocks)
			if err != nil {
				log.Printf("❌ Slack API 오류: %v", err)
				results = append(results, AlertResult{
					Key:   key,
					Error: err.Error(),
				})
				continue
			}
			log.Printf("💬 스레드 답글: %s -> %s", key, threadTS)
		}

		results = append(results, AlertResult{
			Key:       key,
			ThreadTS:  threadTS,
			Status:    webhook.Status,
			Alertname: alert.Labels["alertname"],
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
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func clearCacheHandler(w http.ResponseWriter, r *http.Request) {
	cacheMutex.Lock()
	defer cacheMutex.Unlock()

	threadCache = make(map[string]string)

	response := map[string]string{
		"message": "캐시가 초기화되었습니다",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	// 필수 환경 변수 검증
	if slackBotToken == "" {
		log.Fatal("❌ SLACK_BOT_TOKEN 환경 변수가 필요합니다")
	}
	if slackChannel == "" {
		log.Fatal("❌ SLACK_CHANNEL 환경 변수가 필요합니다")
	}

	// 라우터 설정
	r := mux.NewRouter()
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/alert", alertHandler).Methods("POST")
	r.HandleFunc("/cache", cacheHandler).Methods("GET")
	r.HandleFunc("/cache", clearCacheHandler).Methods("DELETE")

	// 서버 시작
	port, _ := strconv.Atoi(bindPort)
	addr := fmt.Sprintf("%s:%d", bindHost, port)
	
	log.Printf("🚀 DreamSeed Alert Threader 시작됨")
	log.Printf("   환경: %s", environment)
	log.Printf("   채널: %s", slackChannel)
	log.Printf("   주소: http://%s", addr)
	log.Printf("   엔드포인트: POST /alert, GET /health")
	
	log.Fatal(http.ListenAndServe(addr, r))
}

