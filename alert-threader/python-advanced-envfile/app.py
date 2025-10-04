import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI, Request
import httpx

# === Environment Variables ===
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_CHANNEL   = os.environ["SLACK_CHANNEL"]  # 권장: 채널 ID(Cxxxx)
ENV             = os.getenv("ENVIRONMENT", "staging")
THREAD_STORE    = os.getenv("THREAD_STORE", "file")   # file|redis
THREAD_STORE_FILE = os.getenv("THREAD_STORE_FILE", "/var/lib/alert-threader/threads.json")
REDIS_URL       = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_KEY_PREFIX= os.getenv("REDIS_KEY_PREFIX", "threader:ts")

# === App ===
app = FastAPI()
_thread_cache: Dict[str, str] = {}   # key -> thread_ts
_redis = None

# === Utilities ===
def sev_color(sev: str) -> str:
    sev = (sev or "info").lower()
    return {"critical": "#E01E5A", "warning": "#ECB22E"}.get(sev, "#2EB67D")

def sev_emoji(sev: str) -> str:
    return {"critical": "🚨", "warning": "⚠️"}.get((sev or "info").lower(), "ℹ️")

def thread_key(alert: dict) -> str:
    name = alert["labels"].get("alertname", "unknown")
    sev  = alert["labels"].get("severity", "info")
    # 필요시 cluster/service 등 라벨을 더 포함하세요.
    return f"{name}|{sev}|{ENV}"

# === Storage (File / Redis) ===
def _ensure_parent(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def load_cache_file():
    global _thread_cache
    p = Path(THREAD_STORE_FILE)
    if p.exists():
        try:
            _thread_cache = json.loads(p.read_text("utf-8"))
        except Exception:
            _thread_cache = {}
    else:
        _thread_cache = {}

def save_cache_file():
    if THREAD_STORE != "file":
        return
    _ensure_parent(THREAD_STORE_FILE)
    tmp = THREAD_STORE_FILE + ".tmp"
    Path(tmp).write_text(json.dumps(_thread_cache), encoding="utf-8")
    Path(tmp).replace(THREAD_STORE_FILE)

async def load_cache_redis():
    global _thread_cache, _redis
    try:
        import redis.asyncio as redis
    except Exception:
        raise RuntimeError("Install redis client: pip install redis")
    _redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    # 해시 키 1개로 관리 (필드: thread_key, 값: ts) or prefix key-value
    # 여기선 prefix KV 방식을 사용
    # load는 지연(조회 시)로도 충분하므로 여기선 skip (필요시 scan 구현)
    _thread_cache = {}  # 로컬 캐시도 병행 사용

async def store_get_ts(key: str) -> Optional[str]:
    if THREAD_STORE == "redis":
        ts = _thread_cache.get(key)
        if ts:
            return ts
        v = await _redis.get(f"{REDIS_KEY_PREFIX}:{key}")
        if v:
            _thread_cache[key] = v
        return v
    # file
    return _thread_cache.get(key)

async def store_set_ts(key: str, ts: str):
    if THREAD_STORE == "redis":
        await _redis.set(f"{REDIS_KEY_PREFIX}:{key}", ts)
        _thread_cache[key] = ts
        return
    # file
    _thread_cache[key] = ts
    save_cache_file()

# === Slack payload (Block Kit + attachments color) ===
def build_blocks(summary: str, sev: str, description: str, labels: Dict[str,str]):
    emoji = sev_emoji(sev)
    fields = [
        {"type": "mrkdwn", "text": f"*Severity:*\n`{sev}`"},
        {"type": "mrkdwn", "text": f"*Environment:*\n`{ENV}`"},
    ]
    # 유용한 라벨 몇 개 노출(필요시 확장)
    for k in ("alertname","instance","job"):
        if k in labels:
            fields.append({"type": "mrkdwn", "text": f"*{k}:*\n`{labels[k]}`"})
    blocks = [
        {"type": "header", "text": {"type":"plain_text", "text": f"{emoji} {summary}", "emoji": True}},
        {"type": "section", "fields": fields},
    ]
    if description:
        blocks.append({"type":"section","text":{"type":"mrkdwn","text":description}})
    blocks.append({"type":"context","elements":[{"type":"mrkdwn","text":f"`env={ENV}`"}]})
    return blocks

async def slack_post_message(text: str, blocks=None, thread_ts: Optional[str]=None, color: Optional[str]=None):
    """
    Slack chat.postMessage with optional blocks and thread_ts.
    attachments.color는 BlockKit 전체 구조와 별개로 버튼/색 강조에 유용.
    """
    payload = {
        "channel": SLACK_CHANNEL,
        "text": text,  # fallback/plain
        "unfurl_links": False,
        "unfurl_media": False,
    }
    if blocks:
        payload["blocks"] = blocks
    if thread_ts:
        payload["thread_ts"] = thread_ts
    if color:
        payload["attachments"] = [{"color": color}]
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post("https://slack.com/api/chat.postMessage", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack error: {data}")
        return data

# === Startup ===
@app.on_event("startup")
async def on_startup():
    if THREAD_STORE == "redis":
        await load_cache_redis()
    else:
        load_cache_file()

# === Webhook ===
@app.post("/alert")
async def alert(request: Request):
    body = await request.json()
    status = body.get("status")         # firing|resolved
    alerts = body.get("alerts", [])
    results = []
    for a in alerts:
        labels = a.get("labels", {})
        ann    = a.get("annotations", {})
        key    = thread_key(a)
        ts     = await store_get_ts(key)
        summary = ann.get("summary") or labels.get("alertname","(no summary)")
        description = ann.get("description","")
        sev = labels.get("severity","info")
        color = sev_color(sev)
        if status == "resolved":
            text = f"[{ENV}] ✅ RESOLVED: {summary}"
            blocks = build_blocks(f"RESOLVED — {summary}", sev, description, labels)
        else:
            text = f"[{ENV}] {sev.upper()} — {summary}"
            blocks = build_blocks(summary, sev, description, labels)
        # thread parent 없으면 새 메시지 → ts 저장
        if not ts:
            data = await slack_post_message(text, blocks=blocks, thread_ts=None, color=color)
            ts = data["ts"]
            await store_set_ts(key, ts)
        else:
            await slack_post_message(text, blocks=blocks, thread_ts=ts, color=color)
        results.append({"key": key, "thread_ts": ts, "status": status})
    return {"ok": True, "count": len(results), "results": results}

# === Health Check ===
@app.get("/health")
async def health():
    resp = {
        "status": "healthy",
        "environment": ENV,
        "channel": SLACK_CHANNEL,
        "thread_store": THREAD_STORE,
        "cached_threads": len(_thread_cache),
    }
    
    if THREAD_STORE == "redis" and _redis:
        try:
            await _redis.ping()
            resp["redis_status"] = "connected"
        except Exception as e:
            resp["redis_status"] = f"disconnected: {e}"
            resp["status"] = "degraded"
    
    return resp

# === Stats ===
@app.get("/stats")
async def stats():
    resp = {
        "cached_threads": len(_thread_cache),
        "thread_store": THREAD_STORE,
        "environment": ENV,
    }
    
    if THREAD_STORE == "redis" and _redis:
        try:
            info = await _redis.info("memory", "clients", "keyspace")
            resp["redis_info"] = info
        except Exception as e:
            resp["redis_info_error"] = str(e)
    
    return resp

# === Cache Management ===
@app.get("/cache")
async def get_cache():
    return {
        "thread_store": THREAD_STORE,
        "cached_threads_count": len(_thread_cache),
        "cached_threads": _thread_cache,
    }

@app.delete("/cache")
async def clear_cache():
    global _thread_cache
    _thread_cache = {}
    
    if THREAD_STORE == "file":
        try:
            Path(THREAD_STORE_FILE).unlink(missing_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting cache file: {e}")
    elif THREAD_STORE == "redis" and _redis:
        try:
            # Redis에서 모든 키 삭제 (주의: 프로덕션에서는 더 안전한 방법 사용)
            keys = await _redis.keys(f"{REDIS_KEY_PREFIX}:*")
            if keys:
                await _redis.delete(*keys)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error clearing Redis cache: {e}")
    
    return {"ok": True, "message": "Cache cleared"}

