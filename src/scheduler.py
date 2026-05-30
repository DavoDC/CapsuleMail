"""Filename parser, date logic, and letter state tracking."""

import re
from datetime import date
from pathlib import Path

_SEND_PATTERN = re.compile(r"SEND-(\d{4}-\d{2}-\d{2})\.md$")
_DELIVERED_PREFIX = "Status: Delivered"


def parse_send_date(filename: str) -> date | None:
    """Return the send date from a filename, or None if not a scheduled letter."""
    m = _SEND_PATTERN.search(filename)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def is_due(send_date: date) -> bool:
    """Return True if send_date is today or in the past."""
    return send_date <= date.today()


def _is_delivered(filepath: str) -> bool:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline()
        return first_line.startswith(_DELIVERED_PREFIX)
    except OSError:
        return False


def get_pending_letters(letters_dir: str) -> list[str]:
    """Return paths of .md letters that are due and not yet delivered."""
    try:
        paths = list(Path(letters_dir).glob("*.md"))
    except OSError:
        return []

    pending = []
    for p in paths:
        send_date = parse_send_date(p.name)
        if send_date is None:
            continue
        if not is_due(send_date):
            continue
        if _is_delivered(str(p)):
            continue
        pending.append(str(p))
    return pending


def mark_delivered(filepath: str, timestamp: str) -> None:
    """Prepend 'Status: Delivered <timestamp>' to the letter file. Idempotent."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith(_DELIVERED_PREFIX):
        return
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{_DELIVERED_PREFIX} {timestamp}\n{content}")
