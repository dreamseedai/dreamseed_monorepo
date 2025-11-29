"""
모니터링 적용 예시
==================
감사 로그 + Prometheus 메트릭 + trace_id 전파
"""

from fastapi import FastAPI
from shared.monitoring.middleware import AuditMetricsMiddleware, setup_structlog
from shared.monitoring.metrics import router as metrics_router

# structlog 설정 (앱 시작 시 한 번만)
setup_structlog()

app = FastAPI(title="SeedTest API", version="1.0.0")

# 감사 로그 + Prometheus 미들웨어
app.add_middleware(
    AuditMetricsMiddleware, service_name="seedtest-api", service_version="v1"
)

# 메트릭 엔드포인트 (/metrics, /healthz, /readyz)
app.include_router(metrics_router)


@app.get("/")
def root():
    """루트 엔드포인트"""
    return {"message": "SeedTest API with Monitoring"}


@app.get("/api/v1/test")
def test():
    """테스트 엔드포인트"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
