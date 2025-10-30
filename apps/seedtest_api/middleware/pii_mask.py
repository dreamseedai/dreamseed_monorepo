from __future__ import annotations

import logging
import re
from typing import Iterable, List, Optional

from ..settings import Settings


def _compile_default_patterns() -> List[re.Pattern[str]]:
    patterns: List[re.Pattern[str]] = []
    # email
    patterns.append(re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"))
    # phone numbers (simple; international or local with dashes/spaces)
    patterns.append(re.compile(r"\+?\d[\d\s\-]{7,}\d"))
    return patterns


def _mask_value(val: str) -> str:
    # Replace most of the content, keep last 2 chars for debugging context
    if len(val) <= 2:
        return "**"
    return "***" + val[-2:]


def scrub_text(text: str, compiled_patterns: Iterable[re.Pattern[str]]) -> str:
    out = text
    for pat in compiled_patterns:
        out = pat.sub(lambda m: _mask_value(m.group(0)), out)
    return out


class PIIMaskFilter(logging.Filter):
    """Logging filter to scrub PII from log records.

    - Applies regex-based scrubbing to record.getMessage()
    - Redacts common key-value shaped patterns for configured PII keys
    """

    def __init__(self, name: str = ""):
        super().__init__(name)
        s = Settings()
        self.enabled = bool(s.LOG_SCRUB_PII)
        self.keys: List[str] = [
            "name",
            "full_name",
            "email",
            "phone",
            "mobile",
            "address",
            "student_name",
        ]
        if s.PII_KEYS:
            # override/extend if provided
            self.keys = list(dict.fromkeys([*self.keys, *s.PII_KEYS]))
        self.patterns: List[re.Pattern[str]] = []
        if s.ENABLE_DEFAULT_PII_REGEX:
            self.patterns.extend(_compile_default_patterns())
        # Key-value like: key=value or "key": "value"
        self.key_value_patterns: List[re.Pattern[str]] = [
            re.compile(rf"(\b{re.escape(k)}\b\s*[:=]\s*)([^,\s\]]+)", re.IGNORECASE)
            for k in self.keys
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.enabled:
            return True
        try:
            msg = record.getMessage()
            if msg and isinstance(msg, str):
                # Regex scrubbing (email/phone)
                scrubbed = scrub_text(msg, self.patterns)
                # Key-value scrubbing
                for kv_pat in self.key_value_patterns:
                    scrubbed = kv_pat.sub(lambda m: f"{m.group(1)}***", scrubbed)
                # Mutate record message for output
                record.msg = scrubbed
                record.args = None
        except Exception:
            # Fail-open: never break logging
            return True
        return True


def install_pii_masking() -> None:
    """Attach the filter to root and common loggers (idempotent)."""
    flt = PIIMaskFilter()
    root = logging.getLogger()
    for h in root.handlers:
        # Avoid duplicate addition
        if not any(isinstance(f, PIIMaskFilter) for f in h.filters):
            h.addFilter(flt)
    # Common framework loggers
    for name in ("uvicorn", "uvicorn.access", "fastapi"):
        lg = logging.getLogger(name)
        for h in lg.handlers:
            if not any(isinstance(f, PIIMaskFilter) for f in h.filters):
                h.addFilter(flt)
