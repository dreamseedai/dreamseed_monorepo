# backend/user_pattern_api.py
from fastapi import APIRouter
from typing import Dict
from pydantic import BaseModel
import os
import json

router = APIRouter()

USER_PATTERN_DIR = os.path.join(
    os.path.dirname(__file__), "../frontend/src/data/user-patterns"
)
os.makedirs(USER_PATTERN_DIR, exist_ok=True)


class UserPatternRequest(BaseModel):
    user_id: str
    patterns: Dict[str, str]


@router.get("/api/user-patterns/{user_id}")
def get_user_patterns(user_id: str):
    filepath = os.path.join(USER_PATTERN_DIR, f"{user_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@router.post("/api/user-patterns")
def save_user_patterns(req: UserPatternRequest):
    filepath = os.path.join(USER_PATTERN_DIR, f"{req.user_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(req.patterns, f, ensure_ascii=False, indent=2)
    return {"status": "saved"}
