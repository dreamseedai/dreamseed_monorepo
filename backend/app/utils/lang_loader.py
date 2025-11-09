import json
from fastapi import Request


def load_translation(lang_code: str) -> dict:
    try:
        with open(f"./backend/lang/{lang_code}.json", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


async def get_lang_context(request: Request) -> dict:
    # 1. 우선 URL 쿼리에서 읽기
    lang = request.query_params.get("lang", "en")

    # 2. (추후 확장 가능: request.headers.get("Accept-Language"))
    return load_translation(lang)
