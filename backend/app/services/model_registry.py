# app/services/model_registry.py
from typing import Dict

model_registry: Dict[str, str] = {}


def register_model(name: str, version: str = "unknown"):
    model_registry[name] = version


def get_registered_models():
    return model_registry
