from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://dreamseedai.com",
    "https://staging.dreamseedai.com",
]
COOKIE_DOMAIN = ".dreamseedai.com"  # adjust per environment

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # preflight cache
)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/api/auth/me")
def me():
    resp = Response(content='{"ok": true}', media_type="application/json")
    resp.set_cookie(
        key="ds_session",
        value="example",
        httponly=True,
        secure=True,
        samesite="none",
        domain=COOKIE_DOMAIN,
        path="/",
        max_age=7*24*3600,
    )
    return resp