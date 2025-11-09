"""
Feature Flags
기능 플래그 관리
"""
from typing import Dict, Any


def feature_enabled(policy: Dict[str, Any], flag: str) -> bool:
    """
    기능 플래그 활성화 여부 체크
    
    Args:
        policy: 정책 번들 딕셔너리
        flag: 기능 플래그 이름 (예: "risk_engine", "exam_pipeline")
        
    Returns:
        활성화되어 있으면 True, 아니면 False
    """
    return bool(policy.get("feature_flags", {}).get(flag, False))


def get_enabled_features(policy: Dict[str, Any]) -> Dict[str, bool]:
    """
    모든 기능 플래그 상태 반환
    
    Args:
        policy: 정책 번들 딕셔너리
        
    Returns:
        기능 플래그 딕셔너리
    """
    return policy.get("feature_flags", {})
