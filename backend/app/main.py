import os
from dotenv import load_dotenv  # type: ignore[import-not-found]
from fastapi import FastAPI  # type: ignore[import-not-found]
from pydantic import BaseModel  # type: ignore[import-not-found]
from typing import List


# ✅ .env 로드 및 확인
load_dotenv()
print("✅ ENV CHECK:", os.getenv("OPENAI_API_KEY"))

# ✅ FastAPI 인스턴스 생성
app = FastAPI()

# ✅ Governance Middleware 장착
try:
    from app.middleware.policy import GovernanceMiddleware
    app.add_middleware(GovernanceMiddleware)
    print("✅ Governance Middleware enabled")
except Exception as e:
    print(f"⚠️  Governance Middleware disabled: {e}")

@app.get("/__ok")
def ok():
    return {"ok": True}


# ✅ Governance 핫리로드 엔드포인트
@app.post("/internal/policy/reload")
def reload_policy():
    """정책 번들 핫리로드 (재기동 없이 반영)"""
    try:
        from app.policy.loader import reload_policy_bundle, load_policy_bundle
        from app.governance_settings import governance_settings
        
        reload_policy_bundle()  # 캐시 클리어
        
        # 다시 로드
        new_policy = load_policy_bundle(governance_settings.POLICY_BUNDLE_PATH)
        
        return {
            "ok": True,
            "bundle_id": new_policy.get("bundle_id"),
            "phase": new_policy.get("phase"),
            "reloaded_at": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/internal/policy/status")
def policy_status():
    """현재 정책 번들 상태 조회"""
    try:
        from app.middleware.policy import POLICY
        from app.governance_settings import governance_settings
        
        if POLICY is None:
            return {"ok": False, "message": "Policy bundle not loaded"}
        
        return {
            "ok": True,
            "bundle_id": POLICY.get("bundle_id"),
            "phase": POLICY.get("phase"),
            "version": POLICY.get("version"),
            "strict_mode": governance_settings.POLICY_STRICT_MODE,
            "feature_flags": POLICY.get("feature_flags", {}),
            "rbac_enabled": POLICY.get("rbac", {}).get("enabled", True),
            "roles_count": len(POLICY.get("rbac", {}).get("roles", []))
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

"""
라우터를 동적으로 임포트합니다. 외부 의존성(openai 등)으로 인해 일부 모듈이
임포트에 실패하더라도 부팅이 가능하도록 안전 가드로 감쌉니다.
"""

def _try_import(module_path: str, attr: str | None = None):
    try:
        mod = __import__(module_path, fromlist=['*'])
        return getattr(mod, attr) if attr else mod
    except Exception as e:
        print(f"[router-skip] {module_path}: {e}")
        return None

routers = []

# app.routes.* (DB 의존이 상대적으로 적은 내부 라우트들)
for mod, attr in [
    ("app.routes.recall_api", "router"),
    ("app.routes.pattern_api", "router"),
    ("app.routes.dev_status", "router"),
    ("app.routes.dev_ws", "router"),
    ("app.routes.status", "router"),
    ("app.routes.recommend", "router"),
    ("app.routes.emotion_log_routes", "router"),
]:
    r = _try_import(mod, attr)
    if r:
        routers.append(r)

# app.api.* (일부는 openai/DB 등 외부 의존 → 실패 시 스킵)
for mod in [
    "app.api.emotion_analysis_api",
    "app.api.emotion_api",
    "app.api.emotion_log_api",
    "app.api.emotion_gpt_translate",
    "app.api.chat_api",
    "app.api.pronunciation_analysis_api",
    "app.api.recommend_collab",
    "app.api.recommendation_api",
    "app.api.recommendation_log_api",
    "app.api.strategy_api",
    "app.api.whisper_api",
    "app.api.whisper_feedback_api",
    "app.api.emotion_strategy_api",
    "app.api.gpt_recommendation_api",
    "app.api.admin_memo_api",
]:
    r = _try_import(mod, "router")
    if r:
        routers.append(r)

# 외부/별도 모듈 (선택적)
ar = _try_import("common_analytics.routers", "analytics_router")
if ar:
    routers.append(ar)

cr = _try_import("creator_assist_api", "router")
if cr:
    routers.append(cr)

# ✅ 라우터 통합 등록 (성공한 라우터만)
for router in routers:
    app.include_router(router)

# ✅ 보강: /api/chat 라우터가 누락될 수 있어 직접 포함 시도
try:
    from app.api import chat_api as _chat_api  # type: ignore
    app.include_router(_chat_api.router)
except Exception as _e:
    print("[router-skip-fallback] app.api.chat_api:", _e)


# ✅ 샘플 추천 API (테스트용)
class RecommendRequest(BaseModel):
    mode: str
    category: str
    keywords: List[str]


class RecommendItem(BaseModel):
    title: str
    type: str
    source: str
    url: str


@app.post("/api/recommend", response_model=List[RecommendItem])
def recommend(req: RecommendRequest):
    prompt = f"추천할 {req.mode} 콘텐츠: 카테고리={req.category}, 키워드={', '.join(req.keywords)}"
    print(f"🔍 Prompt: {prompt}")  # 디버깅용 출력
    return [
        RecommendItem(
            title="청춘 블루스",
            type="video",
            source="YouTube",
            url="https://example.com/1",
        ),
        RecommendItem(
            title="감성의 순간",
            type="video",
            source="YouTube",
            url="https://example.com/2",
        ),
    ]
