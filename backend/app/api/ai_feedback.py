"""
AI Feedback API for Phase 1 MVP
Provides AI-powered feedback for student answers using Ollama
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Feedback"])

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:32b-instruct-q4_0"


class FeedbackRequest(BaseModel):
    question_id: str
    question_title: str
    question_content: str | None = None
    student_answer: str
    subject: str | None = None


class FeedbackResponse(BaseModel):
    question_id: str
    feedback: str
    model_used: str


async def generate_feedback_ollama(
    question_title: str,
    question_content: str | None,
    student_answer: str,
    subject: str | None,
) -> str:
    """Generate AI feedback using Ollama"""

    # Construct prompt
    prompt_parts = [
        f"과목: {subject}" if subject else "",
        f"문제: {question_title}",
        f"문제 설명: {question_content}" if question_content else "",
        f"학생 답안: {student_answer}",
        "",
        "위 학생의 답안을 평가하고 건설적인 피드백을 제공하세요.",
        "피드백은 한글로 3-5줄 정도로 작성하고, 다음을 포함하세요:",
        "1. 답안의 강점",
        "2. 개선이 필요한 부분",
        "3. 구체적인 학습 제안",
    ]

    prompt = "\n".join([p for p in prompt_parts if p])

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 500,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "피드백을 생성할 수 없습니다.")
    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        raise HTTPException(status_code=504, detail="AI 피드백 생성 시간 초과")
    except httpx.HTTPError as e:
        logger.error(f"Ollama HTTP error: {e}")
        raise HTTPException(status_code=503, detail="AI 서비스에 연결할 수 없습니다")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500, detail="피드백 생성 중 오류가 발생했습니다"
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(request: FeedbackRequest):
    """
    Generate AI feedback for a student's answer

    - **question_id**: Question identifier
    - **question_title**: Title of the question
    - **question_content**: Optional detailed question content
    - **student_answer**: Student's submitted answer
    - **subject**: Optional subject (e.g., math, physics, chemistry)
    """

    feedback = await generate_feedback_ollama(
        question_title=request.question_title,
        question_content=request.question_content,
        student_answer=request.student_answer,
        subject=request.subject,
    )

    return FeedbackResponse(
        question_id=request.question_id,
        feedback=feedback,
        model_used=MODEL_NAME,
    )


@router.get("/health")
async def health_check():
    """Check if Ollama service is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            return {
                "status": "healthy",
                "ollama_available": True,
                "models": model_names,
                "default_model": MODEL_NAME,
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "ollama_available": False,
            "error": str(e),
        }
