"""Persistent settings.

Two stores:
- .env            -> API keys (ANTHROPIC_API_KEY)
- data/settings.json -> everything else: selected model, per-tab remembered prompts
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
SETTINGS_PATH = BASE_DIR / "data" / "settings.json"


def get_api_key() -> str:
    load_dotenv(ENV_PATH, override=True)
    return os.getenv("ANTHROPIC_API_KEY", "")


def save_api_key(key: str) -> None:
    if not ENV_PATH.exists():
        ENV_PATH.touch()
    set_key(str(ENV_PATH), "ANTHROPIC_API_KEY", key)


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def get_tab_setting(tab_id: str, key: str, default=None):
    return load_settings().get("tabs", {}).get(tab_id, {}).get(key, default)


def set_tab_setting(tab_id: str, key: str, value) -> None:
    settings = load_settings()
    settings.setdefault("tabs", {}).setdefault(tab_id, {})[key] = value
    save_settings(settings)


def get_selected_model() -> str:
    return load_settings().get("selected_model", "")


def set_selected_model(model: str) -> None:
    settings = load_settings()
    settings["selected_model"] = model
    save_settings(settings)


# Used by tabs that ask the AI for a large structured response (Voice Editor, Readability
# Editor). One shared, user-adjustable setting instead of a hardcoded value per tab -- a
# value that's fine for a short scene of dialogue can still truncate on a 100-line audit or
# a full-script read, and raising it shouldn't require a code change each time it happens.
DEFAULT_MAX_OUTPUT_TOKENS = 16000


def get_max_output_tokens() -> int:
    return load_settings().get("max_output_tokens", DEFAULT_MAX_OUTPUT_TOKENS)


def set_max_output_tokens(value: int) -> None:
    settings = load_settings()
    settings["max_output_tokens"] = value
    save_settings(settings)
