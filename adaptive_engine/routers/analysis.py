"""Score Analysis API Router

성적 분석 API 엔드포인트
=======================

Endpoints:
- GET /api/analysis/{session_id} : 세션별 성적 분석 리포트 조회
- POST /api/analysis/batch : 여러 세션의 성적 분석 일괄 처리
"""

from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from adaptive_engine.services.score_analysis import (
    ScoreAnalysisService,
    ScoreAnalysisReport,
)


router = APIRouter(prefix="/api/analysis", tags=["score-analysis"])


# ==============================================================================
# Request/Response Models
# ==============================================================================

class AnalysisConfig(BaseModel):
    """분석 설정"""
    engine: str = Field(
        default="hybrid",
        description="분석 엔진: 'irt', 'mixed_effects', 'hybrid'"
    )
    include_forecast: bool = Field(
        default=True,
        description="성장 예측 포함 여부"
    )
    include_benchmark: bool = Field(
        default=True,
        description="비교 기준 포함 여부"
    )
    scale_A: float = Field(
        default=100.0,
        description="척도 점수 변환 계수 A"
    )
    scale_B: float = Field(
        default=500.0,
        description="척도 점수 변환 계수 B"
    )


class ResponseItem(BaseModel):
    """응답 데이터 항목"""
    item_id: str
    correct: bool
    a: float = Field(default=1.0, description="변별력")
    b: float = Field(default=0.0, description="난이도")
    c: float = Field(default=0.0, description="추측도")
    topic: Optional[str] = Field(default=None, description="토픽")
    time_spent_sec: Optional[float] = Field(default=None, description="소요 시간(초)")


class AnalysisRequest(BaseModel):
    """분석 요청"""
    student_id: str
    session_id: str
    responses: List[ResponseItem]
    config: Optional[AnalysisConfig] = None


class BatchAnalysisRequest(BaseModel):
    """일괄 분석 요청"""
    requests: List[AnalysisRequest]
    use_mixed_effects: bool = Field(
        default=True,
        description="혼합효과 모형 사용 여부 (전체 응답 데이터 활용)"
    )


# ==============================================================================
# Dependency Injection
# ==============================================================================

def get_analysis_service(
    engine: str = "hybrid",
    scale_A: float = 100.0,
    scale_B: float = 500.0,
) -> ScoreAnalysisService:
    """분석 서비스 인스턴스 생성"""
    return ScoreAnalysisService(
        engine=engine,
        scale_A=scale_A,
        scale_B=scale_B,
    )


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/", response_model=dict)
def analyze_session(
    request: AnalysisRequest,
) -> dict:
    """단일 세션 성적 분석
    
    학생의 응답 데이터를 기반으로 종합 성적 분석 리포트를 생성합니다.
    
    분석 내용:
    - 능력 추정 (θ, SE, 척도 점수)
    - 토픽별 강약점 분석
    - 맞춤형 학습 추천
    - 성적 성장 예측 (선택)
    - 비교 기준 (백분위) (선택)
    
    Examples
    --------
    ```
    POST /api/analysis/
    {
      "student_id": "student123",
      "session_id": "session456",
      "responses": [
        {"item_id": "q1", "correct": true, "a": 1.2, "b": 0.5, "c": 0.2, "topic": "대수"},
        {"item_id": "q2", "correct": false, "a": 1.0, "b": -0.3, "c": 0.2, "topic": "기하"}
      ],
      "config": {
        "engine": "mixed_effects",
        "include_forecast": true,
        "include_benchmark": true
      }
    }
    ```
    """
    if not request.responses:
        raise HTTPException(status_code=400, detail="No responses provided")
    
    # 설정
    config = request.config or AnalysisConfig()
    
    # 서비스 생성
    service = ScoreAnalysisService(
        engine=config.engine,
        scale_A=config.scale_A,
        scale_B=config.scale_B,
    )
    
    # 응답 데이터 변환
    responses = [r.model_dump() for r in request.responses]
    
    # 분석 실행
    try:
        report = service.generate_report(
            student_id=request.student_id,
            session_id=request.session_id,
            responses=responses,
            all_responses=None,  # 단일 세션이므로 혼합효과 모형 미사용
            include_forecast=config.include_forecast,
            include_benchmark=config.include_benchmark,
        )
        
        return report.to_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/batch", response_model=dict)
def analyze_batch(
    request: BatchAnalysisRequest,
) -> dict:
    """여러 세션 일괄 분석
    
    여러 학생의 응답 데이터를 한 번에 분석합니다.
    혼합효과 모형을 사용하여 학생 능력과 문항 난이도를 동시에 추정합니다.
    
    Examples
    --------
    ```
    POST /api/analysis/batch
    {
      "requests": [
        {
          "student_id": "student1",
          "session_id": "session1",
          "responses": [...]
        },
        {
          "student_id": "student2",
          "session_id": "session2",
          "responses": [...]
        }
      ],
      "use_mixed_effects": true
    }
    ```
    """
    if not request.requests:
        raise HTTPException(status_code=400, detail="No requests provided")
    
    # 전체 응답 수집 (혼합효과 모형용)
    all_responses = []
    if request.use_mixed_effects:
        for req in request.requests:
            for resp in req.responses:
                resp_dict = resp.model_dump()
                resp_dict["student_id"] = req.student_id
                all_responses.append(resp_dict)
    
    # 각 요청별로 분석
    reports = []
    for req in request.requests:
        config = req.config or AnalysisConfig()
        
        # 혼합효과 모형 사용 시 엔진 강제 설정
        if request.use_mixed_effects and len(all_responses) >= 50:
            config.engine = "mixed_effects"
        
        service = ScoreAnalysisService(
            engine=config.engine,
            scale_A=config.scale_A,
            scale_B=config.scale_B,
        )
        
        responses = [r.model_dump() for r in req.responses]
        
        try:
            report = service.generate_report(
                student_id=req.student_id,
                session_id=req.session_id,
                responses=responses,
                all_responses=all_responses if request.use_mixed_effects else None,
                include_forecast=config.include_forecast,
                include_benchmark=config.include_benchmark,
            )
            
            reports.append(report.to_dict())
            
        except Exception as e:
            # 개별 실패는 에러 정보만 기록하고 계속 진행
            reports.append({
                "student_id": req.student_id,
                "session_id": req.session_id,
                "error": str(e),
            })
    
    return {
        "n_requests": len(request.requests),
        "n_success": sum(1 for r in reports if "error" not in r),
        "n_failed": sum(1 for r in reports if "error" in r),
        "reports": reports,
    }


@router.get("/health")
def health_check() -> dict:
    """분석 서비스 상태 확인"""
    return {
        "status": "ok",
        "service": "score-analysis",
        "engines_available": ["irt", "mixed_effects", "hybrid"],
    }


# ==============================================================================
# 문항 난이도 보정 엔드포인트 (관리자용)
# ==============================================================================

@router.post("/calibrate-items", response_model=dict)
def calibrate_items(
    responses: List[dict],
    prior_mean: float = Query(default=0.0),
    prior_var: float = Query(default=1.0),
) -> dict:
    """문항 난이도 보정 (관리자용)
    
    많은 학생의 응답 데이터를 사용하여 문항 난이도를 보정합니다.
    혼합효과 모형을 사용하여 공정한 난이도 추정을 수행합니다.
    
    Parameters
    ----------
    responses : List[dict]
        전체 응답 데이터 (student_id, item_id, correct, a, b, c 포함)
        
    prior_mean, prior_var : float
        학생 능력의 사전 분포 파라미터
        
    Returns
    -------
    dict
        보정된 문항 난이도 정보
    """
    if len(responses) < 50:
        raise HTTPException(
            status_code=400,
            detail="At least 50 responses required for item calibration"
        )
    
    try:
        from shared.mixed_effects import fit_mixed_effects
        
        # 혼합효과 모형 적용
        abilities, difficulties = fit_mixed_effects(
            responses,
            prior_mean=prior_mean,
            prior_var=prior_var,
            verbose=False,
        )
        
        # 결과 정리
        item_calibrations = {
            item_id: {
                "b_calibrated": diff.b,
                "se": diff.se,
                "n_responses": diff.n_responses,
            }
            for item_id, diff in difficulties.items()
        }
        
        student_abilities_summary = {
            student_id: {
                "theta": ability.theta,
                "se": ability.se,
                "n_responses": ability.n_responses,
            }
            for student_id, ability in abilities.items()
        }
        
        return {
            "n_students": len(abilities),
            "n_items": len(difficulties),
            "item_calibrations": item_calibrations,
            "student_abilities": student_abilities_summary,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calibration failed: {str(e)}"
        )

