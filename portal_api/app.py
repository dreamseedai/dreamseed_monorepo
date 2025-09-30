import sys
import json
import os
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import jwt
import bcrypt
import asyncio
from typing import List, Optional, Literal

# In production (deployed under /srv/portal_api/current), add monorepo root
# if shared/ was bundled next to app, prefer relative import path
_here = Path(__file__).resolve()
_maybe_shared = _here.parent / "shared"
if _maybe_shared.exists():
    shared_parent = str(_here.parent)
    if shared_parent not in sys.path:
        sys.path.insert(0, shared_parent)
else:
    _root = _here.parents[1]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from shared.auth.dependencies import get_current_user, set_session_cookie, clear_session_cookie


app = FastAPI(title="Portal API", version="0.1.0", root_path="/api", redirect_slashes=False)

# Dev CORS convenience; production goes through same-origin Nginx proxy
ALLOWED_ORIGINS = [
    "https://dreamseedai.com",
    "https://www.dreamseedai.com",
    "http://localhost:5172",
    "http://127.0.0.1:5172",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def _ok() -> dict:
    return {"ok": True}

@app.get("/__ok")
def ok_root() -> dict:
    return _ok()

@app.get("/api/__ok")
def ok_api() -> dict:
    return _ok()


# (root_path="/api")이므로 /api/__ok와 동일


def _version() -> dict:
    # 기본값은 환경변수, version.json이 있으면 병합/우선
    ver = {
        "version": os.getenv("APP_VERSION", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
    }
    try:
        p = Path(__file__).parent / "version.json"
        if p.exists():
            j = json.loads(p.read_text(encoding="utf-8"))
            ver["version"] = j.get("version", j.get("git_sha", ver["version"]))
    except Exception:
        pass
    return {"version": ver["version"]}

@app.get("/version")
def version_root() -> dict:
    return _version()

@app.get("/api/version")
def version_api() -> dict:
    return _version()


@app.get("/billing/stripe/expiring")
def billing_expiring(days: int = 3, limit: int = 10):
    # Demo stub: empty list to satisfy frontend without 404
    return {"items": []}

@app.get("/api/billing/stripe/expiring")
def billing_expiring_api(days: int = 3, limit: int = 10):
    return billing_expiring(days, limit)

class LoginRequest(BaseModel):
    username: str
    password: str


# JWT cookie-based auth (minimal)
AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me")
JWT_ALGO = "HS256"
JWT_COOKIE = "ds_session"
JWT_TTL_HOURS = 12

class LoginReq(BaseModel):
    email: EmailStr
    password: str

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@dreamseedai.com")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")  # bcrypt hash

def verify_user(email: str, password: str):
    # If ADMIN_PASSWORD_HASH is unset, allow demo default password for convenience
    if not ADMIN_PASSWORD_HASH:
        if password == "Test1234!":
            display_name = (email or "").strip() or "Admin"
            return {"id": "1", "role": "admin", "name": display_name}
        return None
    try:
        ok = bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode())
    except Exception:
        ok = False
    if ok:
        display_name = (email or "").strip() or "Admin"
        return {"id": "1", "role": "admin", "name": display_name}
    return None

@app.post("/auth/login")
def auth_login(body: LoginReq, resp: Response):
    user = verify_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    payload = {
        "sub": user["id"],
        "role": user["role"],
        "name": user.get("name"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_TTL_HOURS),
    }
    token = jwt.encode(payload, AUTH_SECRET, algorithm=JWT_ALGO)
    resp.set_cookie(
        key=JWT_COOKIE,
        value=token,
        max_age=JWT_TTL_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return {"access_token": token, "token_type": "bearer"}

# Duplicate routes under /api/* for proxies that don't set ASGI root_path
@app.post("/api/auth/login")
def auth_login_api(body: LoginReq, resp: Response):
    return auth_login(body, resp)

def _extract_token(req: Request) -> Optional[str]:
    tok = req.cookies.get(JWT_COOKIE)
    if tok:
        return tok
    auth = req.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


@app.get("/auth/me")
def auth_me(req: Request):
    tok = _extract_token(req)
    if not tok:
        return {"anon": True}
    try:
        data = jwt.decode(tok, AUTH_SECRET, algorithms=[JWT_ALGO])
        return {"anon": False, "id": data.get("sub"), "role": data.get("role"), "name": data.get("name")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid")


@app.post("/auth/refresh")
def auth_refresh(req: Request, resp: Response):
    tok = _extract_token(req)
    if not tok:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        data = jwt.decode(tok, AUTH_SECRET, algorithms=[JWT_ALGO], options={"verify_exp": False})
        payload = {
            "sub": data.get("sub"),
            "role": data.get("role"),
            "name": data.get("name"),
            "exp": datetime.utcnow() + timedelta(hours=JWT_TTL_HOURS),
        }
        new_token = jwt.encode(payload, AUTH_SECRET, algorithm=JWT_ALGO)
        resp.set_cookie(
            key=JWT_COOKIE,
            value=new_token,
            max_age=JWT_TTL_HOURS * 3600,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
        )
        return {"access_token": new_token, "token_type": "bearer"}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid")

@app.get("/api/auth/me")
def auth_me_api(req: Request):
    return auth_me(req)

@app.post("/api/auth/refresh")
def auth_refresh_api(req: Request, resp: Response):
    return auth_refresh(req, resp)

@app.post("/auth/logout")
def auth_logout(resp: Response):
    resp.delete_cookie(JWT_COOKIE, path="/")
    return {"ok": True}

@app.post("/api/auth/logout")
def auth_logout_api(resp: Response):
    return auth_logout(resp)


@app.post("/api/login")
def login(payload: LoginRequest):
    # demo: any non-empty credentials accepted
    if not payload.username or not payload.password:
        return JSONResponse(status_code=400, content={"detail": "bad credentials"})
    resp = JSONResponse(content={"ok": True})
    set_session_cookie(resp, {"username": payload.username})
    return resp


@app.post("/api/logout")
def logout():
    resp = JSONResponse(content={"ok": True})
    clear_session_cookie(resp)
    return resp


@app.get("/api/me")
def me(user=Depends(get_current_user)):
    return {"user": user}


# ─────────────────────────────────────────────────────────────────────────────
# Recommend API (formalized)
# ─────────────────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    country: str = Field(..., description="Target country code, e.g., US or CA")
    grade: str = Field(..., description="Grade code, e.g., G9-G12")
    goal: Optional[str] = Field(None, description="Optional goal keyword")


class RecommendItem(BaseModel):
    title: str
    summary: Optional[str] = None
    icon: Optional[str] = None
    targetCountry: Optional[str] = None
    slug: Optional[str] = None


def _recommend_core(country: str, grade: Optional[str], goal: Optional[str]) -> List[RecommendItem]:
    cu = (country or '').upper()
    gr = (grade or '').upper()
    items: List[RecommendItem] = []
    if cu == 'US':
        items = [
            RecommendItem(title="US 입시 로드맵", summary="입시 준비 전반 가이드", icon="🎓", targetCountry="US", slug="us-roadmap"),
            RecommendItem(title="SAT 1500+ 전략", summary="점수대별 학습 로드맵", icon="📝", targetCountry="US", slug="exams/sat"),
            RecommendItem(title="AP 선택 전략", summary="과목 조합과 난이도", icon="📚", targetCountry="US", slug="exams/ap"),
        ]
    elif cu == 'CA':
        items = [
            RecommendItem(title="캐나다 학기별 로드맵", summary="고등 필수 과목 및 활동", icon="🍁", targetCountry="CA", slug="ca-roadmap"),
            RecommendItem(title="OUAC 준비 가이드", summary="온타리오 지원 절차", icon="🗂️", targetCountry="CA", slug="exams/ouac"),
        ]
    return items


@app.get("/recommend/plan")
def recommend_plan(country: str, grade: Optional[str] = None, goal: Optional[str] = None):
    items = _recommend_core(country=country, grade=grade, goal=goal)
    return {"items": [i.dict() for i in items]}


@app.get("/api/recommend/plan")
def recommend_plan_api(country: str, grade: Optional[str] = None, goal: Optional[str] = None):
    return recommend_plan(country, grade, goal)


@app.post("/recommend")
def recommend_post(req: RecommendRequest):
    items = _recommend_core(country=req.country, grade=req.grade, goal=req.goal)
    return items


@app.post("/api/recommend")
def recommend_post_api(req: RecommendRequest):
    return recommend_post(req)

# Accept trailing-slash variants to avoid redirects that may break POST
@app.post("/recommend/", include_in_schema=False)
def recommend_post_slash(req: RecommendRequest):
    return recommend_post(req)

@app.post("/api/recommend/", include_in_schema=False)
def recommend_post_api_slash(req: RecommendRequest):
    return recommend_post(req)


# No-op GET aliases to neutralize accidental GETs (prevents UI overwrite)
@app.get("/api/recommend", include_in_schema=False)
def recommend_get_noop() -> Response:
    return Response(status_code=204)

@app.get("/api/recommend/", include_in_schema=False)
def recommend_get_noop_slash() -> Response:
    return Response(status_code=204)


# ─────────────────────────────────────────────────────────────────────────────
# Admin-only: whitelisted sudo ops with interactive password
# ─────────────────────────────────────────────────────────────────────────────

class OpsRunReq(BaseModel):
    command_id: Literal[
        "nginx_reload",
        "audit_mpc",
        "audit_portal",
    ]
    args: Optional[List[str]] = None
    sudo_password: Optional[str] = None  # If NOPASSWD not configured
    timeout_seconds: Optional[int] = 20


def require_admin(req: Request):
    tok = req.cookies.get(JWT_COOKIE)
    if not tok:
        raise HTTPException(status_code=401, detail="not authenticated")
    try:
        data = jwt.decode(tok, AUTH_SECRET, algorithms=[JWT_ALGO])
        if data.get("role") != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        return {"id": data.get("sub"), "name": data.get("name"), "role": data.get("role")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid")


def _resolve_command(req: OpsRunReq) -> List[str]:
    mapping = {
        "nginx_reload": ["/usr/local/sbin/nxreload_safe"],
        "audit_mpc": ["/usr/local/sbin/audit_mpc.sh"],
        "audit_portal": ["/usr/local/sbin/audit_portal.sh"],
    }
    base = mapping.get(req.command_id)
    if not base:
        raise HTTPException(status_code=400, detail="unknown command")
    if req.args:
        base = base + list(req.args)
    return base


async def _run_with_optional_sudo(cmd: List[str], sudo_password: Optional[str], timeout_seconds: int):
    # Prefer direct run; if password provided, wrap with sudo -S -k
    if sudo_password:
        full = ["sudo", "-S", "-k", "--"] + cmd
        proc = await asyncio.create_subprocess_exec(
            *full,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=(sudo_password + "\n").encode("utf-8")),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=504, detail="command timeout")
        return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")
    else:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=504, detail="command timeout")
        return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


@app.post("/api/ops/run")
async def ops_run(body: OpsRunReq, _admin=Depends(require_admin)):
    cmd = _resolve_command(body)
    started = datetime.utcnow()
    code, out, err = await _run_with_optional_sudo(cmd, body.sudo_password, body.timeout_seconds or 20)
    dur_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
    # Limit payload sizes
    def _cap(s: str) -> str:
        return s if len(s) <= 20000 else s[:20000] + "\n…(truncated)…"
    return {
        "ok": code == 0,
        "exit_code": code,
        "stdout": _cap(out),
        "stderr": _cap(err),
        "duration_ms": dur_ms,
        "command": cmd,
    }

