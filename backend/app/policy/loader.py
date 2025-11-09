"""
Policy Bundle Loader
정책 번들 로더
"""
import json
import pathlib
from functools import lru_cache
from typing import Dict, Any


@lru_cache(maxsize=1)
def load_policy_bundle(path: str) -> Dict[str, Any]:
    """
    정책 번들 로드 (캐시됨)
    
    Args:
        path: 정책 번들 JSON 파일 경로
        
    Returns:
        정책 번들 딕셔너리
        
    Raises:
        RuntimeError: 파일이 없거나 필수 키가 없을 경우
    """
    p = pathlib.Path(path)
    
    if not p.exists():
        raise RuntimeError(f"Policy bundle not found: {path}")
    
    try:
        data = json.loads(p.read_text("utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in policy bundle: {e}")
    
    # 필수 키 검증
    required_keys = ("bundle_id", "rbac", "feature_flags")
    for key in required_keys:
        if key not in data:
            raise RuntimeError(f"Invalid policy bundle: missing '{key}'")
    
    return data


def reload_policy_bundle():
    """정책 번들 캐시 클리어 (핫리로드용)"""
    load_policy_bundle.cache_clear()
