from pydantic import BaseModel
import os
from pathlib import Path
from .services.filters import parse_int_list, parse_str_list

try:
    # Optional: load .env if present for local dev
    from dotenv import load_dotenv  # type: ignore
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    # Do not crash if python-dotenv isn't installed in prod
    pass


def _get_str(name: str) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else None


def _get_float(name: str) -> float | None:
    v = os.getenv(name)
    return float(v) if v not in (None, "") else None


def _get_int(name: str, default: int | None = None) -> int | None:
    v = os.getenv(name)
    if v in (None, ""):
        return default
    return int(v)


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
    BANK_DIFF_MIN: float | None = _get_float("BANK_DIFF_MIN")
    BANK_DIFF_MAX: float | None = _get_float("BANK_DIFF_MAX")
    BANK_SAMPLE_K: int | None = _get_int("BANK_SAMPLE_K")
    BANK_SAMPLE_P: float | None = _get_float("BANK_SAMPLE_P")
    BANK_ORG_ID: int | None = _get_int("BANK_ORG_ID")
    BANK_TOPIC_IDS: str | None = os.getenv("BANK_TOPIC_IDS")  # comma/space separated ints
    BANK_TAGS: str | None = os.getenv("BANK_TAGS")  # comma/space separated strings
    # 0이면 매 쿼리마다 재탐지, None/미설정이면 기본 300초
    TAGS_KIND_TTL_SEC: int | None = _get_int("TAGS_KIND_TTL_SEC", default=300)
    # Adaptive selection policy (ops-tunable)
    CAT_TOP_N: int = int(os.getenv("CAT_TOP_N", "3"))  # randomesque top-N
    CAT_AVOID_REPEAT_K: int = int(os.getenv("CAT_AVOID_REPEAT_K", "2"))  # avoid same topic for last K
    CAT_REPEAT_PENALTY: float = float(os.getenv("CAT_REPEAT_PENALTY", "0.15"))  # 15% penalty by default
    CAT_BLUEPRINT: str | None = os.getenv("CAT_BLUEPRINT")  # JSON mapping of topic_id->target proportion
    CAT_MAX_EXPOSURE: int | None = _get_int("CAT_MAX_EXPOSURE")
    # Optional Sympson-Hetter acceptance probabilities per item id; load from service/store if provided
    CAT_ACCEPTANCE_SOURCE: str | None = os.getenv("CAT_ACCEPTANCE_SOURCE")
    CAT_ACCEPTANCE_P_DEFAULT: float | None = _get_float("CAT_ACCEPTANCE_P_DEFAULT")
    # Stopping rules (variable/fixed length)
    CAT_SEM_THRESHOLD: float | None = _get_float("CAT_SEM_THRESHOLD")  # e.g., 0.3 for variable-length
    CAT_MAX_ITEMS: int | None = _get_int("CAT_MAX_ITEMS")  # hard cap
    CAT_MIN_ITEMS: int | None = _get_int("CAT_MIN_ITEMS")  # minimum before SE stop allowed
    CAT_MAX_TIME_SECONDS: int | None = _get_int("CAT_MAX_TIME_SECONDS")  # time limit
    CAT_MODE: str = os.getenv("CAT_MODE", "VARIABLE").upper()  # VARIABLE | FIXED
    # Additional timing controls
    CAT_MIN_TEST_TIME_SECONDS: int | None = _get_int("CAT_MIN_TEST_TIME_SECONDS")
    CAT_ITEM_COOLDOWN_SECONDS: int | None = _get_int("CAT_ITEM_COOLDOWN_SECONDS")
    # Starting item randomization
    CAT_START_RANDOMIZED: bool = os.getenv("CAT_START_RANDOMIZED", "true").lower() == "true"
    CAT_START_BAND_WIDTH: float = float(os.getenv("CAT_START_BAND_WIDTH", "0.5"))  # +/- around theta0
    CAT_START_TOP_N: int = int(os.getenv("CAT_START_TOP_N", "3"))
    # Hard content rule: avoid immediate same-topic unless info advantage is significant
    CAT_AVOID_SAME_TOPIC_HARD: bool = os.getenv("CAT_AVOID_SAME_TOPIC_HARD", "true").lower() == "true"
    CAT_SAME_TOPIC_TOLERANCE: float = float(os.getenv("CAT_SAME_TOPIC_TOLERANCE", "0.05"))  # 5% tolerance
    # Exposure logging
    CAT_EXPOSURE_LOG_PATH: str | None = os.getenv("CAT_EXPOSURE_LOG_PATH")

    @property
    def bank_topic_ids(self) -> list[int]:
        return parse_int_list(self.BANK_TOPIC_IDS)

    @property
    def bank_tags(self) -> list[str]:
        return parse_str_list(self.BANK_TAGS)


settings = Settings()

