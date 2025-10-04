from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import time

# Allowed origins - NEVER use '*' with allow_credentials=True
ALLOWED_ORIGINS = [
    "https://dreamseedai.com",
    "https://staging.dreamseedai.com",
    "https://www.dreamseedai.com"
]

# Cookie domain for cross-site cookies (환경 변수로 제어)
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".dreamseedai.com")

app = FastAPI()

# CORS middleware configuration
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
    """Health check endpoint for monitoring with dependency checks"""
    health_status = {
        "status": "ok", 
        "service": "dreamseed-api",
        "version": "1.0.0",
        "timestamp": int(time.time()),
        "dependencies": {}
    }
    
    # Check database connection (if applicable)
    try:
        # Add your database health check here
        # db_status = check_database_connection()
        health_status["dependencies"]["database"] = "ok"
    except Exception as e:
        health_status["dependencies"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection (if applicable)
    try:
        # Add your Redis health check here
        # redis_status = check_redis_connection()
        health_status["dependencies"]["redis"] = "ok"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check external API dependencies
    try:
        # Add external API health checks here
        health_status["dependencies"]["external_apis"] = "ok"
    except Exception as e:
        health_status["dependencies"]["external_apis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/auth/me")
def me():
    # Example cookie set compatible with cross-site
    resp = Response(content='{"ok": true}', media_type="application/json")
    
    # For cross-site cookies you must use Secure + SameSite=None + Domain
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

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "dreamseed-api"}

# Example endpoint with proper CORS handling
@app.options("/api/{path:path}")
def options_handler(path: str):
    """Handle preflight OPTIONS requests"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://dreamseedai.com",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        }
    )

# WebSocket endpoints are CORS-exempt (documented)
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     # WebSocket connections don't use CORS
#     pass
