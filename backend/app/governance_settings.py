"""
Governance Settings
거버넌스 환경 변수 및 설정
"""

from pydantic_settings import BaseSettings


class GovernanceSettings(BaseSettings):
    """거버넌스 설정"""

    # 정책 번들 설정
    POLICY_BUNDLE_ID: str = "phase1"
    GOVERNANCE_PHASE: int = 1
    POLICY_STRICT_MODE: str = "enforce"  # "soft" or "enforce"
    POLICY_BUNDLE_PATH: str = "governance/compiled/policy_bundle_phase1.json"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 싱글톤 인스턴스
governance_settings = GovernanceSettings()
