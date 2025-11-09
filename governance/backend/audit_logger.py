"""
정책 계층 감사 로깅 모듈.

정책 평가 이벤트를 구조화된 JSON 로그로 표준 출력에 남기기 위해 로거를 설정하고,
정책 평가 결과(허용/거부) 및 에러를 로깅하는 함수를 제공합니다.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Union

# Logger configuration for audit logs
logger = logging.getLogger("governance.audit")
# Avoid adding multiple handlers if logger already configured
if not logger.handlers:
    level_name = os.getenv("AUDIT_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        level = logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    # Output only the message (JSON) without default formatting
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def log_policy_evaluation(
    user_id: str,
    user_role: str,
    resource_path: str,
    resource_method: str,
    policy_name: str,
    result: str,
    duration_ms: Union[int, float],
    reason: Optional[str] = None
) -> None:
    """
    정책 평가 결과(허용 또는 거부)를 JSON 형식으로 로깅합니다.

    Parameters:
        user_id (str): 사용자 식별자.
        user_role (str): 사용자의 역할.
        resource_path (str): 요청 리소스의 경로.
        resource_method (str): HTTP 메서드 (GET, POST 등).
        policy_name (str): 평가된 정책의 이름.
        result (str): 정책 평가 결과 ("allow" 또는 "deny").
        duration_ms (int or float): 정책 평가에 소요된 시간(밀리초).
        reason (str, optional): 거부 사유가 있는 경우 해당 사유.

    Note:
        result 값이 "allow"나 "deny"가 아닌 경우, 이 함수는 해당 이벤트를 에러 레벨로 로깅하고 ValueError를 발생시킵니다.
        에러 이벤트를 로깅하려면 log_policy_error 함수를 사용하세요.
    """
    # Create the log record as a dict
    timestamp = datetime.now(timezone.utc).isoformat()
    log_record = {
        "timestamp": timestamp,
        "event_type": "policy_evaluation",
        "user_id": user_id,
        "user_role": user_role,
        "resource_path": resource_path,
        "resource_method": resource_method,
        "policy_name": policy_name,
        "result": result,
        "duration_ms": int(duration_ms) if not isinstance(duration_ms, int) else duration_ms
    }
    if reason is not None:
        log_record["reason"] = reason

    # Log at appropriate level based on result
    res = result.lower()
    if res == "allow":
        logger.info(json.dumps(log_record, ensure_ascii=False))
    elif res == "deny":
        logger.warning(json.dumps(log_record, ensure_ascii=False))
    else:
        # Log invalid result as error and raise exception
        log_record["result"] = "error"
        log_record["reason"] = log_record.get("reason", "") or "Invalid policy evaluation result"
        logger.error(json.dumps(log_record, ensure_ascii=False))
        raise ValueError(f"Invalid result for log_policy_evaluation: {result}. Use log_policy_error for errors.")


def log_policy_error(
    user_id: str,
    user_role: str,
    resource_path: str,
    resource_method: str,
    policy_name: str,
    reason: str,
    duration_ms: Union[int, float]
) -> None:
    """
    정책 평가 중 발생한 에러를 JSON 형식으로 로깅합니다.

    Parameters:
        user_id (str): 사용자 식별자.
        user_role (str): 사용자의 역할.
        resource_path (str): 요청 리소스의 경로.
        resource_method (str): HTTP 메서드 (GET, POST 등).
        policy_name (str): 평가 중이던 정책의 이름.
        reason (str): 에러의 상세 원인 또는 메시지.
        duration_ms (int or float): 에러가 발생하기까지 소요된 시간(밀리초).
    """
    # Create the log record for the error event
    timestamp = datetime.now(timezone.utc).isoformat()
    log_record = {
        "timestamp": timestamp,
        "event_type": "policy_evaluation",
        "user_id": user_id,
        "user_role": user_role,
        "resource_path": resource_path,
        "resource_method": resource_method,
        "policy_name": policy_name,
        "result": "error",
        "duration_ms": int(duration_ms) if not isinstance(duration_ms, int) else duration_ms,
        "reason": reason
    }
    # Log at ERROR level
    logger.error(json.dumps(log_record, ensure_ascii=False))
