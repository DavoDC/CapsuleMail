"""CapsuleMail daemon - poll loop entry point."""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import schedule
import time
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from scheduler import get_pending_letters, mark_delivered
from sender import send_letter

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        print(f"[ERROR] Config not found: {_CONFIG_PATH}")
        print("Copy config/config.example.yaml to config/config.yaml and fill in your settings.")
        sys.exit(1)
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def log_delivery(logs_dir: str, filepath: str, status: str, timestamp: str) -> None:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(logs_dir) / "deliveries.csv"
    write_header = not log_path.exists()
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "file", "status"])
        writer.writerow([timestamp, Path(filepath).name, status])


def poll(config: dict) -> None:
    letters_dir = config["paths"]["letters_dir"]
    logs_dir = config["paths"]["logs_dir"]

    pending = get_pending_letters(letters_dir)
    if not pending:
        return

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {len(pending)} letter(s) due")

    for filepath in pending:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            send_letter(filepath, config)
            mark_delivered(filepath, timestamp)
            log_delivery(logs_dir, filepath, "delivered", timestamp)
            print(f"  [OK] Delivered: {Path(filepath).name}")
        except Exception as e:
            log_delivery(logs_dir, filepath, f"failed: {e}", timestamp)
            print(f"  [FAIL] {Path(filepath).name}: {e}")


def main() -> None:
    config = load_config()

    send_time = config["scheduling"].get("send_time", "09:00")
    print(f"CapsuleMail started. Checking daily at {send_time} and polling hourly.")
    print(f"Letters dir: {config['paths']['letters_dir']}")
    print("Press Ctrl+C to stop.\n")

    # Poll immediately on startup to catch anything already due
    poll(config)

    # Hourly poll + dedicated daily send at the configured time
    schedule.every().hour.do(poll, config=config)
    schedule.every().day.at(send_time).do(poll, config=config)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
