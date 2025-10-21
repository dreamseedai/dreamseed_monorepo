import json
import os
from functools import lru_cache
from jsonschema import Draft202012Validator


@lru_cache(maxsize=16)
def _load_schema(schema_path: str) -> dict:
	with open(schema_path, "r", encoding="utf-8") as f:
		return json.load(f)


def validate_event(data: dict, schema_path: str) -> None:
	"""Validate event against JSON Schema.
	Raises ValueError with joined messages on first failure batch.
	"""
	schema = _load_schema(os.path.abspath(schema_path))
	validator = Draft202012Validator(schema)
	errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
	if errors:
		msg = "; ".join([e.message for e in errors])
		raise ValueError(msg)
