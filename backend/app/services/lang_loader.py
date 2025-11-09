# backend/app/services/lang_loader.py
import json
import os

TRANSLATION_DIR = os.path.join(os.path.dirname(__file__), "../i18n")


def load_translation(lang_code: str = "ko") -> dict:
    """
    주어진 언어 코드에 해당하는 번역 JSON 파일을 로드합니다.
    기본값은 'ko'입니다.
    """
    file_path = os.path.join(TRANSLATION_DIR, f"{lang_code}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 번역 파일을 찾을 수 없습니다: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"❌ JSON 파싱 오류: {file_path}")
        return {}
