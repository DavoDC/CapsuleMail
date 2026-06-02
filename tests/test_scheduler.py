"""Tests for scheduler.py - filename parsing, date logic, header read/write."""

import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from scheduler import parse_send_date, is_due, get_pending_letters, get_upcoming_letters, mark_delivered


class TestParseSendDate:
    def test_valid_filename(self):
        assert parse_send_date("futureme-letter-2026-05-10-SEND-2027-05-10.md") == date(2027, 5, 10)

    def test_valid_any_prefix(self):
        assert parse_send_date("my-note-SEND-2030-12-25.md") == date(2030, 12, 25)

    def test_no_send_pattern_returns_none(self):
        assert parse_send_date("no-date-here.md") is None

    def test_not_a_md_file(self):
        assert parse_send_date("futureme-letter-SEND-2027-05-10.txt") is None

    def test_malformed_date_returns_none(self):
        assert parse_send_date("letter-SEND-2027-13-01.md") is None

    def test_missing_day_returns_none(self):
        assert parse_send_date("letter-SEND-2027-05.md") is None

    def test_send_date_at_end_of_name(self):
        assert parse_send_date("SEND-2025-01-15.md") == date(2025, 1, 15)


class TestIsDue:
    def test_past_date_is_due(self):
        yesterday = date.today() - timedelta(days=1)
        assert is_due(yesterday) is True

    def test_today_is_due(self):
        assert is_due(date.today()) is True

    def test_future_date_not_due(self):
        tomorrow = date.today() + timedelta(days=1)
        assert is_due(tomorrow) is False

    def test_far_future_not_due(self):
        far = date(2099, 1, 1)
        assert is_due(far) is False


class TestGetPendingLetters:
    def test_returns_due_letters_only(self, tmp_path):
        past = date.today() - timedelta(days=1)
        future = date.today() + timedelta(days=1)
        (tmp_path / f"letter-SEND-{past}.md").write_text("hello past")
        (tmp_path / f"letter-SEND-{future}.md").write_text("hello future")
        (tmp_path / "no-date.md").write_text("ignored")

        pending = get_pending_letters(str(tmp_path))
        assert len(pending) == 1
        assert f"SEND-{past}" in pending[0]

    def test_already_delivered_letter_excluded(self, tmp_path):
        past = date.today() - timedelta(days=1)
        f = tmp_path / f"letter-SEND-{past}.md"
        f.write_text("Status: Delivered 2026-05-01 09:00:00\n\nhello")

        pending = get_pending_letters(str(tmp_path))
        assert pending == []

    def test_empty_dir_returns_empty(self, tmp_path):
        assert get_pending_letters(str(tmp_path)) == []

    def test_nonexistent_dir_returns_empty(self):
        assert get_pending_letters("/nonexistent/path/xyz") == []


class TestGetUpcomingLetters:
    def test_returns_future_and_past_undelivered(self, tmp_path):
        past = date.today() - timedelta(days=3)
        future = date.today() + timedelta(days=5)
        (tmp_path / f"letter-SEND-{past}.md").write_text("past")
        (tmp_path / f"letter-SEND-{future}.md").write_text("future")

        result = get_upcoming_letters(str(tmp_path))
        assert len(result) == 2

    def test_excludes_delivered(self, tmp_path):
        past = date.today() - timedelta(days=1)
        f = tmp_path / f"letter-SEND-{past}.md"
        f.write_text("Status: Delivered 2026-05-01 09:00:00\nhello")

        result = get_upcoming_letters(str(tmp_path))
        assert result == []

    def test_sorted_by_date(self, tmp_path):
        d1 = date.today() + timedelta(days=10)
        d2 = date.today() + timedelta(days=2)
        d3 = date.today() + timedelta(days=7)
        for d in [d1, d2, d3]:
            (tmp_path / f"letter-SEND-{d}.md").write_text("x")

        result = get_upcoming_letters(str(tmp_path))
        dates = [r[0] for r in result]
        assert dates == sorted(dates)

    def test_empty_dir_returns_empty(self, tmp_path):
        assert get_upcoming_letters(str(tmp_path)) == []

    def test_nonexistent_dir_returns_empty(self):
        assert get_upcoming_letters("/nonexistent/xyz") == []

    def test_includes_today(self, tmp_path):
        today = date.today()
        (tmp_path / f"letter-SEND-{today}.md").write_text("today")
        result = get_upcoming_letters(str(tmp_path))
        assert len(result) == 1
        assert result[0][0] == today


class TestMarkDelivered:
    def test_adds_status_header_to_file(self, tmp_path):
        f = tmp_path / "letter-SEND-2026-05-10.md"
        f.write_text("Dear Future Me,\n\nHello.\n")

        mark_delivered(str(f), "2026-05-10 09:00:00")

        content = f.read_text()
        assert content.startswith("Status: Delivered 2026-05-10 09:00:00\n")
        assert "Dear Future Me," in content

    def test_idempotent_if_already_delivered(self, tmp_path):
        f = tmp_path / "letter-SEND-2026-05-10.md"
        original = "Status: Delivered 2026-05-10 09:00:00\n\nDear Future Me,"
        f.write_text(original)

        mark_delivered(str(f), "2026-05-10 10:00:00")

        assert f.read_text() == original

    def test_preserves_full_body(self, tmp_path):
        body = "Line 1\nLine 2\nLine 3\n"
        f = tmp_path / "letter-SEND-2026-05-10.md"
        f.write_text(body)

        mark_delivered(str(f), "2026-05-10 09:00:00")

        content = f.read_text()
        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content
