from pathlib import Path
from pydantic_settings import BaseSettings
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


class Settings(BaseSettings):
    # API
    API_PREFIX: str = "/api/seedtest"

    # Auth
    JWKS_URL: str = "https://auth.dreamseedai.com/.well-known/jwks.json"
    JWT_ISS: str = "https://auth.dreamseedai.com/"
    JWT_AUD: str = "seedtest-api"
    JWT_PUBLIC_KEY: str | None = None

    # Dev flags
    LOCAL_DEV: bool = False  # loosen auth when true
    APP_ENV: str = "local"

    # Database
    DATABASE_URL: str | None = None

    # CAT hyperparameters
    CAT_PRIOR_MEAN: float = 0.0
    CAT_PRIOR_SD: float = 1.0
    CAT_STEP_CAP: float = 1.0
    CAT_CRITERION: str = "FISHER"  # FISHER | KL
    CAT_KL_DELTA: float = 0.5

    # Item bank loader filters (optional)
    BANK_SUBJECT: str | None = None
    BANK_DIFF_MIN: float | None = None
    BANK_DIFF_MAX: float | None = None
    BANK_SAMPLE_K: int | None = None
    BANK_SAMPLE_P: float | None = None
    BANK_ORG_ID: int | None = None
    BANK_TOPIC_IDS: str | None = None  # comma/space separated ints
    BANK_TAGS: str | None = None  # comma/space separated strings
    TAGS_KIND_TTL_SEC: int | None = 300

    # Adaptive selection policy
    CAT_TOP_N: int = 3
    CAT_AVOID_REPEAT_K: int = 2
    CAT_REPEAT_PENALTY: float = 0.15
    CAT_BLUEPRINT: str | None = None
    CAT_MAX_EXPOSURE: int | None = None
    CAT_ACCEPTANCE_SOURCE: str | None = None
    CAT_ACCEPTANCE_P_DEFAULT: float | None = None

    # Stopping rules
    CAT_SEM_THRESHOLD: float | None = None
    CAT_MAX_ITEMS: int | None = None
    CAT_MIN_ITEMS: int | None = None
    CAT_MAX_TIME_SECONDS: int | None = None
    CAT_MODE: str = "VARIABLE"  # VARIABLE | FIXED

    # Additional timing controls
    CAT_MIN_TEST_TIME_SECONDS: int | None = None
    CAT_ITEM_COOLDOWN_SECONDS: int | None = None

    # Starting item randomization
    CAT_START_RANDOMIZED: bool = True
    CAT_START_BAND_WIDTH: float = 0.5
    CAT_START_TOP_N: int = 3

    # Content rule
    CAT_AVOID_SAME_TOPIC_HARD: bool = True
    CAT_SAME_TOPIC_TOLERANCE: float = 0.05

    # Exposure logging
    CAT_EXPOSURE_LOG_PATH: str | None = None

    model_config = {
        "env_file": None,  # dotenv loaded manually above if present
        "extra": "ignore",
    }

    @property
    def bank_topic_ids(self) -> list[int]:
        return parse_int_list(self.BANK_TOPIC_IDS)

    @property
    def bank_tags(self) -> list[str]:
        return parse_str_list(self.BANK_TAGS)


settings = Settings()
