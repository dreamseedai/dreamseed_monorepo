#!/usr/bin/env python3
"""
DreamSeed Alertmanager Slack Threader
Alertmanager webhook을 받아서 Slack Bot API로 스레드 메시지를 전송하는 래퍼 서비스
"""

import os
import time
import hashlib
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "staging")
BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
BIND_PORT = int(os.getenv("BIND_PORT", "9009"))

# 필수 환경 변수 검증
if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN 환경 변수가 필요합니다")
if not SLACK_CHANNEL:
    raise ValueError("SLACK_CHANNEL 환경 변수가 필요합니다")

app = FastAPI(
    title="DreamSeed Alert Threader",
    description="Alertmanager webhook을 Slack 스레드로 변환하는 서비스",
    version="1.0.0"
)

# 스레드 캐시 (실제 운영에서는 Redis나 파일 저장 권장)
thread_cache: Dict[str, str] = {}

def thread_key(alert: dict) -> str:
    """알림의 스레드 키를 생성합니다."""
    name = alert.get("labels", {}).get("alertname", "unknown")
    severity = alert.get("labels", {}).get("severity", "info")
    service = alert.get("labels", {}).get("service", "unknown")
    return f"{name}|{severity}|{service}|{ENVIRONMENT}"

def get_emoji(severity: str) -> str:
    """심각도에 따른 이모지를 반환합니다."""
    emoji_map = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
        "error": "❌",
        "success": "✅"
    }
    return emoji_map.get(severity.lower(), "📢")

def get_color(severity: str) -> str:
    """심각도에 따른 색상을 반환합니다."""
    color_map = {
        "critical": "#E01E5A",
        "warning": "#ECB22E", 
        "info": "#2EB67D",
        "error": "#E01E5A",
        "success": "#2EB67D"
    }
    return color_map.get(severity.lower(), "#2EB67D")

async def slack_chat_post(
    text: str, 
    thread_ts: Optional[str] = None, 
    color: str = "#2EB67D",
    blocks: Optional[List[dict]] = None
) -> dict:
    """Slack API로 메시지를 전송합니다."""
    payload = {
        "channel": SLACK_CHANNEL,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
    if blocks:
        payload["blocks"] = blocks
    
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Slack API 오류: {error_msg}")
                raise RuntimeError(f"Slack API 오류: {error_msg}")
            
            return data
        except httpx.RequestError as e:
            logger.error(f"Slack API 요청 실패: {e}")
            raise

def format_alert_message(alert: dict, status: str) -> tuple[str, List[dict]]:
    """알림 메시지를 포맷팅합니다."""
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    
    alertname = labels.get("alertname", "Unknown")
    severity = labels.get("severity", "info")
    service = labels.get("service", "unknown")
    summary = annotations.get("summary", alertname)
    description = annotations.get("description", "")
    
    emoji = get_emoji(severity)
    color = get_color(severity)
    
    # 상태에 따른 메시지 포맷
    if status == "resolved":
        text = f"*[{ENVIRONMENT}]* ✅ **RESOLVED** - {summary}"
    else:
        text = f"*[{ENVIRONMENT}]* {emoji} **{summary}** (`{severity}`)"
    
    # Slack Block Kit 포맷
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
    ]
    
    if description:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*설명:* {description}"
            }
        })
    
    # 라벨 정보
    label_text = " | ".join([f"`{k}={v}`" for k, v in labels.items() if k in ["alertname", "severity", "service", "instance"]])
    if label_text:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*라벨:* {label_text}"
                }
            ]
        })
    
    return text, blocks

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "channel": SLACK_CHANNEL,
        "cached_threads": len(thread_cache)
    }

@app.post("/alert")
async def alert_webhook(request: Request):
    """Alertmanager webhook 엔드포인트"""
    try:
        body = await request.json()
        status = body.get("status")  # firing / resolved
        alerts = body.get("alerts", [])
        group_key = body.get("groupKey", "")
        
        logger.info(f"Received {len(alerts)} alerts with status: {status}")
        
        results = []
        
        for alert in alerts:
            try:
                key = thread_key(alert)
                thread_ts = thread_cache.get(key)
                
                text, blocks = format_alert_message(alert, status)
                
                # 스레드가 없으면 새 메시지 생성
                if not thread_ts:
                    data = await slack_chat_post(text, thread_ts=None, blocks=blocks)
                    thread_ts = data["ts"]
                    thread_cache[key] = thread_ts
                    logger.info(f"새 스레드 생성: {key} -> {thread_ts}")
                else:
                    # 기존 스레드에 답글
                    await slack_chat_post(text, thread_ts=thread_ts, blocks=blocks)
                    logger.info(f"스레드 답글: {key} -> {thread_ts}")
                
                results.append({
                    "key": key,
                    "thread_ts": thread_ts,
                    "status": status,
                    "alertname": alert.get("labels", {}).get("alertname", "unknown")
                })
                
            except Exception as e:
                logger.error(f"알림 처리 실패: {e}")
                results.append({
                    "key": key if 'key' in locals() else "unknown",
                    "error": str(e)
                })
        
        return {
            "ok": True,
            "count": len(results),
            "status": status,
            "group_key": group_key,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Webhook 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache")
async def get_cache():
    """캐시 상태 조회 (디버깅용)"""
    return {
        "cached_threads": len(thread_cache),
        "threads": thread_cache
    }

@app.delete("/cache")
async def clear_cache():
    """캐시 초기화 (디버깅용)"""
    thread_cache.clear()
    return {"message": "캐시가 초기화되었습니다"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=BIND_HOST,
        port=BIND_PORT,
        log_level="info"
    )

