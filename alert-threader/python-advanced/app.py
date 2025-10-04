#!/usr/bin/env python3
"""
DreamSeed Alertmanager Slack Threader - Advanced Version
- 파일/Redis 기반 thread_ts 영속 저장소
- Slack Block Kit + Attachments 컬러 강조
- 고급 메시지 포맷팅 및 필드 구성
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "staging")
BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
BIND_PORT = int(os.getenv("BIND_PORT", "9009"))

# 저장소 설정
THREAD_STORE = os.getenv("THREAD_STORE", "file")  # file|redis
THREAD_STORE_FILE = os.getenv("THREAD_STORE_FILE", "/var/lib/alert-threader/threads.json")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "threader:ts")

# 필수 환경 변수 검증
if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN 환경 변수가 필요합니다")
if not SLACK_CHANNEL:
    raise ValueError("SLACK_CHANNEL 환경 변수가 필요합니다")

app = FastAPI(
    title="DreamSeed Alert Threader - Advanced",
    description="Alertmanager webhook을 Slack 스레드로 변환하는 고급 서비스",
    version="2.0.0"
)

# 전역 변수
_thread_cache: Dict[str, str] = {}
_redis = None

# === 유틸리티 함수 ===

def get_severity_color(severity: str) -> str:
    """심각도에 따른 색상을 반환합니다."""
    color_map = {
        "critical": "#E01E5A",  # 빨강
        "warning": "#ECB22E",   # 노랑
        "info": "#2EB67D",      # 초록
        "error": "#E01E5A",     # 빨강
        "success": "#2EB67D",   # 초록
        "debug": "#36C5F0",     # 파랑
    }
    return color_map.get(severity.lower(), "#2EB67D")

def get_severity_emoji(severity: str) -> str:
    """심각도에 따른 이모지를 반환합니다."""
    emoji_map = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
        "error": "❌",
        "success": "✅",
        "debug": "🐛",
    }
    return emoji_map.get(severity.lower(), "📢")

def thread_key(alert: dict) -> str:
    """알림의 스레드 키를 생성합니다."""
    labels = alert.get("labels", {})
    name = labels.get("alertname", "unknown")
    severity = labels.get("severity", "info")
    service = labels.get("service", "unknown")
    cluster = labels.get("cluster", "default")
    return f"{name}|{severity}|{service}|{cluster}|{ENVIRONMENT}"

def format_timestamp(timestamp: str) -> str:
    """타임스탬프를 포맷팅합니다."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return timestamp

# === 저장소 관리 (파일/Redis) ===

def ensure_parent_directory(path: str):
    """부모 디렉터리를 생성합니다."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def load_cache_file():
    """파일에서 캐시를 로드합니다."""
    global _thread_cache
    p = Path(THREAD_STORE_FILE)
    if p.exists():
        try:
            _thread_cache = json.loads(p.read_text("utf-8"))
            logger.info(f"파일에서 {len(_thread_cache)}개 스레드 로드됨")
        except Exception as e:
            logger.error(f"파일 캐시 로드 실패: {e}")
            _thread_cache = {}
    else:
        _thread_cache = {}

def save_cache_file():
    """파일에 캐시를 저장합니다."""
    if THREAD_STORE != "file":
        return
    
    try:
        ensure_parent_directory(THREAD_STORE_FILE)
        tmp_file = THREAD_STORE_FILE + ".tmp"
        Path(tmp_file).write_text(json.dumps(_thread_cache, indent=2), encoding="utf-8")
        Path(tmp_file).replace(THREAD_STORE_FILE)
        logger.debug(f"파일에 {len(_thread_cache)}개 스레드 저장됨")
    except Exception as e:
        logger.error(f"파일 캐시 저장 실패: {e}")

async def load_cache_redis():
    """Redis에서 캐시를 로드합니다."""
    global _thread_cache, _redis
    try:
        import redis.asyncio as redis
    except ImportError:
        raise RuntimeError("Redis 클라이언트가 필요합니다: pip install redis")
    
    _redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    _thread_cache = {}  # Redis는 지연 로딩 사용
    logger.info("Redis 연결 초기화됨")

async def store_get_ts(key: str) -> Optional[str]:
    """저장소에서 스레드 ID를 조회합니다."""
    if THREAD_STORE == "redis":
        # 로컬 캐시 먼저 확인
        ts = _thread_cache.get(key)
        if ts:
            return ts
        
        # Redis에서 조회
        try:
            ts = await _redis.get(f"{REDIS_KEY_PREFIX}:{key}")
            if ts:
                _thread_cache[key] = ts
            return ts
        except Exception as e:
            logger.error(f"Redis 조회 실패: {e}")
            return None
    else:
        # 파일 저장소
        return _thread_cache.get(key)

async def store_set_ts(key: str, ts: str):
    """저장소에 스레드 ID를 저장합니다."""
    if THREAD_STORE == "redis":
        try:
            await _redis.set(f"{REDIS_KEY_PREFIX}:{key}", ts)
            _thread_cache[key] = ts
            logger.debug(f"Redis에 스레드 저장: {key} -> {ts}")
        except Exception as e:
            logger.error(f"Redis 저장 실패: {e}")
    else:
        # 파일 저장소
        _thread_cache[key] = ts
        save_cache_file()

# === Slack Block Kit 포맷팅 ===

def build_alert_blocks(alert: dict, status: str) -> List[Dict[str, Any]]:
    """알림을 위한 Slack Block Kit을 구성합니다."""
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    
    alertname = labels.get("alertname", "Unknown")
    severity = labels.get("severity", "info")
    service = labels.get("service", "unknown")
    instance = labels.get("instance", "")
    cluster = labels.get("cluster", "default")
    
    summary = annotations.get("summary", alertname)
    description = annotations.get("description", "")
    runbook_url = annotations.get("runbook_url", "")
    
    emoji = get_severity_emoji(severity)
    
    # 상태에 따른 헤더 텍스트
    if status == "resolved":
        header_text = f"✅ RESOLVED — {summary}"
    else:
        header_text = f"{emoji} {summary}"
    
    # 헤더 블록
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
                "emoji": True
            }
        }
    ]
    
    # 필드 섹션
    fields = [
        {
            "type": "mrkdwn",
            "text": f"*Severity:*\n`{severity.upper()}`"
        },
        {
            "type": "mrkdwn",
            "text": f"*Environment:*\n`{ENVIRONMENT}`"
        },
        {
            "type": "mrkdwn",
            "text": f"*Service:*\n`{service}`"
        },
        {
            "type": "mrkdwn",
            "text": f"*Cluster:*\n`{cluster}`"
        }
    ]
    
    # 인스턴스가 있으면 추가
    if instance:
        fields.append({
            "type": "mrkdwn",
            "text": f"*Instance:*\n`{instance}`"
        })
    
    blocks.append({
        "type": "section",
        "fields": fields
    })
    
    # 설명이 있으면 추가
    if description:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{description}"
            }
        })
    
    # Runbook URL이 있으면 추가
    if runbook_url:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Runbook:* <{runbook_url}|View Runbook>"
            }
        })
    
    # 시간 정보
    starts_at = alert.get("startsAt", "")
    ends_at = alert.get("endsAt", "")
    
    time_info = []
    if starts_at:
        time_info.append(f"Started: {format_timestamp(starts_at)}")
    if ends_at and status == "resolved":
        time_info.append(f"Resolved: {format_timestamp(ends_at)}")
    
    if time_info:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": " | ".join(time_info)
                }
            ]
        })
    
    # 환경 정보
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"`env={ENVIRONMENT}` | `alertname={alertname}`"
            }
        ]
    })
    
    return blocks

def build_alert_attachments(alert: dict, status: str) -> List[Dict[str, Any]]:
    """알림을 위한 Slack Attachments를 구성합니다."""
    labels = alert.get("labels", {})
    severity = labels.get("severity", "info")
    color = get_severity_color(severity)
    
    # 기본 attachment
    attachment = {
        "color": color,
        "fallback": f"[{ENVIRONMENT}] {labels.get('alertname', 'Unknown')}",
    }
    
    # 필드 구성
    fields = []
    
    # 심각도
    fields.append({
        "title": "Severity",
        "value": severity.upper(),
        "short": True
    })
    
    # 환경
    fields.append({
        "title": "Environment",
        "value": ENVIRONMENT,
        "short": True
    })
    
    # 서비스
    if "service" in labels:
        fields.append({
            "title": "Service",
            "value": labels["service"],
            "short": True
        })
    
    # 클러스터
    if "cluster" in labels:
        fields.append({
            "title": "Cluster",
            "value": labels["cluster"],
            "short": True
        })
    
    # 인스턴스
    if "instance" in labels:
        fields.append({
            "title": "Instance",
            "value": labels["instance"],
            "short": True
        })
    
    # Job
    if "job" in labels:
        fields.append({
            "title": "Job",
            "value": labels["job"],
            "short": True
        })
    
    attachment["fields"] = fields
    
    # 설명
    if "description" in alert.get("annotations", {}):
        attachment["text"] = alert["annotations"]["description"]
    
    # 시간 정보
    starts_at = alert.get("startsAt", "")
    if starts_at:
        attachment["ts"] = int(datetime.fromisoformat(starts_at.replace('Z', '+00:00')).timestamp())
    
    return [attachment]

async def slack_post_message(
    text: str,
    blocks: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    thread_ts: Optional[str] = None
) -> dict:
    """Slack API로 메시지를 전송합니다."""
    payload = {
        "channel": SLACK_CHANNEL,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    
    if blocks:
        payload["blocks"] = blocks
    
    if attachments:
        payload["attachments"] = attachments
    
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
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

# === FastAPI 엔드포인트 ===

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행됩니다."""
    logger.info("DreamSeed Alert Threader 시작 중...")
    
    if THREAD_STORE == "redis":
        await load_cache_redis()
    else:
        load_cache_file()
    
    logger.info(f"저장소: {THREAD_STORE}")
    logger.info(f"환경: {ENVIRONMENT}")
    logger.info(f"채널: {SLACK_CHANNEL}")

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    cache_size = len(_thread_cache)
    
    health_data = {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "channel": SLACK_CHANNEL,
        "thread_store": THREAD_STORE,
        "cached_threads": cache_size,
        "timestamp": datetime.now().isoformat()
    }
    
    # Redis 연결 상태 확인
    if THREAD_STORE == "redis" and _redis:
        try:
            await _redis.ping()
            health_data["redis_status"] = "connected"
        except Exception as e:
            health_data["redis_status"] = f"error: {e}"
    
    return health_data

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
                thread_ts = await store_get_ts(key)
                
                labels = alert.get("labels", {})
                annotations = alert.get("annotations", {})
                
                alertname = labels.get("alertname", "Unknown")
                severity = labels.get("severity", "info")
                summary = annotations.get("summary", alertname)
                
                # 메시지 텍스트 (fallback)
                if status == "resolved":
                    text = f"[{ENVIRONMENT}] ✅ RESOLVED: {summary}"
                else:
                    text = f"[{ENVIRONMENT}] {severity.upper()}: {summary}"
                
                # Block Kit 구성
                blocks = build_alert_blocks(alert, status)
                
                # Attachments 구성
                attachments = build_alert_attachments(alert, status)
                
                # 스레드가 없으면 새 메시지 생성
                if not thread_ts:
                    data = await slack_post_message(
                        text=text,
                        blocks=blocks,
                        attachments=attachments,
                        thread_ts=None
                    )
                    thread_ts = data["ts"]
                    await store_set_ts(key, thread_ts)
                    logger.info(f"새 스레드 생성: {key} -> {thread_ts}")
                else:
                    # 기존 스레드에 답글
                    await slack_post_message(
                        text=text,
                        blocks=blocks,
                        attachments=attachments,
                        thread_ts=thread_ts
                    )
                    logger.info(f"스레드 답글: {key} -> {thread_ts}")
                
                results.append({
                    "key": key,
                    "thread_ts": thread_ts,
                    "status": status,
                    "alertname": alertname,
                    "severity": severity
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
            "thread_store": THREAD_STORE,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Webhook 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache")
async def get_cache():
    """캐시 상태 조회 (디버깅용)"""
    return {
        "cached_threads": len(_thread_cache),
        "threads": _thread_cache,
        "thread_store": THREAD_STORE
    }

@app.delete("/cache")
async def clear_cache():
    """캐시 초기화 (디버깅용)"""
    _thread_cache.clear()
    
    if THREAD_STORE == "redis" and _redis:
        try:
            # Redis에서 모든 스레드 키 삭제
            keys = await _redis.keys(f"{REDIS_KEY_PREFIX}:*")
            if keys:
                await _redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis 캐시 초기화 실패: {e}")
    
    return {"message": "캐시가 초기화되었습니다"}

@app.get("/stats")
async def get_stats():
    """통계 정보 조회"""
    stats = {
        "cached_threads": len(_thread_cache),
        "thread_store": THREAD_STORE,
        "environment": ENVIRONMENT,
        "uptime": datetime.now().isoformat()
    }
    
    if THREAD_STORE == "redis" and _redis:
        try:
            # Redis 통계
            info = await _redis.info()
            stats["redis"] = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            stats["redis_error"] = str(e)
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=BIND_HOST,
        port=BIND_PORT,
        log_level="info"
    )

