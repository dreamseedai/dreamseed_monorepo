from pydantic import BaseModel
import os


class Settings(BaseModel):
    API_PREFIX: str = "/api/seedtest"
    JWKS_URL: str = os.getenv("JWKS_URL", "https://auth.dreamseedai.com/.well-known/jwks.json")
    JWT_ISS: str = os.getenv("JWT_ISS", "https://auth.dreamseedai.com/")
    JWT_AUD: str = os.getenv("JWT_AUD", "seedtest-api")
    # 개발 편의: 인증을 완화(LOCAL_DEV=true일 때 Authorization 미검증)
    LOCAL_DEV: bool = os.getenv("LOCAL_DEV", "false").lower() == "true"
    # Optional DB URL for direct service access (SQLAlchemy)
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    # CAT hyperparameters (stage-tunable)
    CAT_PRIOR_MEAN: float = float(os.getenv("CAT_PRIOR_MEAN", "0.0"))
    CAT_PRIOR_SD: float = float(os.getenv("CAT_PRIOR_SD", "1.0"))
    CAT_STEP_CAP: float = float(os.getenv("CAT_STEP_CAP", "1.0"))
    CAT_CRITERION: str = os.getenv("CAT_CRITERION", "FISHER").upper()  # FISHER | KL
    CAT_KL_DELTA: float = float(os.getenv("CAT_KL_DELTA", "0.5"))
    # Item bank loader filters (optional)
    BANK_SUBJECT: str | None = os.getenv("BANK_SUBJECT")
    BANK_DIFF_MIN: float | None = (float(os.getenv("BANK_DIFF_MIN")) if os.getenv("BANK_DIFF_MIN") else None)
    BANK_DIFF_MAX: float | None = (float(os.getenv("BANK_DIFF_MAX")) if os.getenv("BANK_DIFF_MAX") else None)
    BANK_SAMPLE_K: int | None = (int(os.getenv("BANK_SAMPLE_K")) if os.getenv("BANK_SAMPLE_K") else None)
    BANK_SAMPLE_P: float | None = (float(os.getenv("BANK_SAMPLE_P")) if os.getenv("BANK_SAMPLE_P") else None)


settings = Settings()

