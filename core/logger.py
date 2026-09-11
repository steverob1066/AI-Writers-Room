"""Lightweight logging so what the app is doing -- and especially why something failed --
can be inspected from the Log window instead of disappearing once a status label updates.
Not a full logging framework; just enough to troubleshoot from.
"""
import datetime
from pathlib import Path
from typing import Callable, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_PATH = DATA_DIR / "app_log.txt"
RAW_RESPONSES_DIR = DATA_DIR / "raw_responses"

MAX_ENTRIES = 500  # in-memory cap for the Log window; the file on disk keeps everything

_entries: List[str] = []
_subscribers: List[Callable[[str], None]] = []


def subscribe(callback: Callable[[str], None]) -> None:
    """Register a callback fired with each new entry, so the Log window can update live.
    Pair with unsubscribe() when the subscriber goes away (e.g. the window is closed) --
    otherwise repeated open/close cycles pile up permanent listeners."""
    _subscribers.append(callback)


def unsubscribe(callback: Callable[[str], None]) -> None:
    try:
        _subscribers.remove(callback)
    except ValueError:
        pass


def log(tab_id: str, message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{tab_id}] {message}"
    _entries.append(entry)
    del _entries[: -MAX_ENTRIES]
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass  # logging must never be the thing that crashes the app
    for callback in list(_subscribers):
        try:
            callback(entry)
        except Exception:
            pass


def get_entries() -> List[str]:
    return list(_entries)


def clear() -> None:
    _entries.clear()
    try:
        LOG_PATH.write_text("", encoding="utf-8")
    except Exception:
        pass


def save_raw_response(tab_id: str, raw_text: str) -> str:
    """Save a raw AI response that failed to parse, so it can be inspected in full.
    Returns the file path, or "" if saving failed."""
    try:
        RAW_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = RAW_RESPONSES_DIR / f"{tab_id}_{timestamp}.txt"
        path.write_text(raw_text, encoding="utf-8")
        return str(path)
    except Exception:
        return ""
