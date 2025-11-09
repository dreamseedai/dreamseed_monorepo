"""
LLM 라우팅 설정
===============
환경 변수에서 LLM 관련 설정을 로드합니다.
"""
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """LLM 라우팅 설정"""
    
    # DeepSeek 클라우드
    DEEPSEEK_API_KEY: str = ""
    
    # 로컬 LLM 서버
    LOCAL_KO_URL: str = "http://127.0.0.1:9001/v1/chat/completions"
    LOCAL_EN_URL: str = "http://127.0.0.1:9002/v1/chat/completions"
    
    # 기본 언어
    DEFAULT_LANG: str = "ko"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
llm_settings = LLMSettings()
