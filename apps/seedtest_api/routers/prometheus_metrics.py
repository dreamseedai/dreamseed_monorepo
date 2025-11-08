"""Prometheus 메트릭 엔드포인트

FastAPI 애플리케이션의 Prometheus 메트릭을 노출합니다.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
import time

router = APIRouter(tags=["monitoring"])

# HTTP 요청 메트릭
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint']
)

# Governance 정책 메트릭
policy_evaluations_total = Counter(
    'policy_evaluations_total',
    'Total policy evaluations',
    ['action', 'role', 'phase', 'result']
)

policy_evaluation_duration_seconds = Histogram(
    'policy_evaluation_duration_seconds',
    'Policy evaluation duration',
    ['action', 'phase']
)

policy_deny_total = Counter(
    'policy_deny_total',
    'Total policy denials',
    ['action', 'role', 'phase', 'reason']
)

policy_allow_total = Counter(
    'policy_allow_total',
    'Total policy allows',
    ['action', 'role', 'phase']
)

# Governance 번들 메트릭
governance_bundle_loaded = Gauge(
    'governance_bundle_loaded',
    'Governance bundle loaded status',
    ['bundle_id', 'phase']
)

governance_bundle_reload_total = Counter(
    'governance_bundle_reload_total',
    'Total governance bundle reloads',
    ['bundle_id', 'phase', 'status']
)

governance_bundle_reload_duration_seconds = Histogram(
    'governance_bundle_reload_duration_seconds',
    'Governance bundle reload duration',
    ['bundle_id', 'phase']
)

# Feature Flag 메트릭
feature_flag_checks_total = Counter(
    'feature_flag_checks_total',
    'Total feature flag checks',
    ['flag_name', 'result']
)

feature_flag_enabled = Gauge(
    'feature_flag_enabled',
    'Feature flag enabled status',
    ['flag_name', 'phase']
)

# IRT 드리프트 메트릭
irt_drift_detections_total = Counter(
    'irt_drift_detections_total',
    'Total IRT drift detections',
    ['status']
)

irt_drift_flagged_items = Gauge(
    'irt_drift_flagged_items',
    'Number of flagged items in IRT drift detection'
)

irt_drift_detection_duration_seconds = Histogram(
    'irt_drift_detection_duration_seconds',
    'IRT drift detection duration'
)

# 데이터베이스 메트릭
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type']
)

# 애플리케이션 메트릭
app_info = Gauge(
    'app_info',
    'Application information',
    ['version', 'environment']
)

# 초기 설정
app_info.labels(version='0.1.0', environment='development').set(1)


@router.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/health")
async def health():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


# 메트릭 헬퍼 함수들
def record_http_request(method: str, endpoint: str, status: int, duration: float):
    """HTTP 요청 메트릭 기록"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_policy_evaluation(action: str, role: str, phase: str, result: str, duration: float):
    """정책 평가 메트릭 기록"""
    policy_evaluations_total.labels(action=action, role=role, phase=phase, result=result).inc()
    policy_evaluation_duration_seconds.labels(action=action, phase=phase).observe(duration)
    
    if result == "allow":
        policy_allow_total.labels(action=action, role=role, phase=phase).inc()
    elif result == "deny":
        policy_deny_total.labels(action=action, role=role, phase=phase, reason="policy_violation").inc()


def record_bundle_reload(bundle_id: str, phase: str, status: str, duration: float):
    """번들 리로드 메트릭 기록"""
    governance_bundle_reload_total.labels(bundle_id=bundle_id, phase=phase, status=status).inc()
    governance_bundle_reload_duration_seconds.labels(bundle_id=bundle_id, phase=phase).observe(duration)
    
    if status == "success":
        governance_bundle_loaded.labels(bundle_id=bundle_id, phase=phase).set(1)
    else:
        governance_bundle_loaded.labels(bundle_id=bundle_id, phase=phase).set(0)


def record_feature_flag_check(flag_name: str, result: bool, phase: str):
    """Feature Flag 체크 메트릭 기록"""
    feature_flag_checks_total.labels(flag_name=flag_name, result=str(result)).inc()
    feature_flag_enabled.labels(flag_name=flag_name, phase=phase).set(1 if result else 0)


def record_irt_drift_detection(status: str, flagged_items: int, duration: float):
    """IRT 드리프트 감지 메트릭 기록"""
    irt_drift_detections_total.labels(status=status).inc()
    irt_drift_flagged_items.set(flagged_items)
    irt_drift_detection_duration_seconds.observe(duration)


def record_db_query(query_type: str, duration: float, error: bool = False):
    """데이터베이스 쿼리 메트릭 기록"""
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)
    if error:
        db_errors_total.labels(error_type="query_error").inc()


__all__ = [
    "router",
    "record_http_request",
    "record_policy_evaluation",
    "record_bundle_reload",
    "record_feature_flag_check",
    "record_irt_drift_detection",
    "record_db_query",
]
