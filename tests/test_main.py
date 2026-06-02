"""Tests for main.py - log_delivery (CSV I/O) and poll (core delivery loop)."""

import csv
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from main import log_delivery, poll


class TestLogDelivery:
    def test_creates_file_with_header_on_first_call(self, tmp_path):
        log_delivery(str(tmp_path), "/letters/note.md", "delivered", "2026-05-10 09:00:00")
        log_path = tmp_path / "deliveries.csv"
        assert log_path.exists()
        rows = list(csv.reader(log_path.open()))
        assert rows[0] == ["timestamp", "file", "status"]
        assert rows[1] == ["2026-05-10 09:00:00", "note.md", "delivered"]

    def test_appends_on_second_call_no_duplicate_header(self, tmp_path):
        log_delivery(str(tmp_path), "/letters/a.md", "delivered", "2026-05-10 09:00:00")
        log_delivery(str(tmp_path), "/letters/b.md", "failed: timeout", "2026-05-10 10:00:00")
        rows = list(csv.reader((tmp_path / "deliveries.csv").open()))
        assert len(rows) == 3  # header + 2 data rows
        assert rows[1][1] == "a.md"
        assert rows[2][1] == "b.md"
        assert rows[2][2] == "failed: timeout"

    def test_creates_parent_directory_if_missing(self, tmp_path):
        nested = tmp_path / "logs" / "deep"
        log_delivery(str(nested), "/letters/x.md", "delivered", "2026-05-10 09:00:00")
        assert (nested / "deliveries.csv").exists()

    def test_records_only_filename_not_full_path(self, tmp_path):
        log_delivery(str(tmp_path), "/very/long/path/my-letter.md", "delivered", "2026-05-10 09:00:00")
        rows = list(csv.reader((tmp_path / "deliveries.csv").open()))
        assert rows[1][1] == "my-letter.md"


class TestPoll:
    def _config(self, tmp_path):
        return {
            "paths": {"letters_dir": str(tmp_path / "letters"), "logs_dir": str(tmp_path / "logs")},
        }

    def test_no_pending_letters_returns_immediately(self, tmp_path):
        config = self._config(tmp_path)
        with (
            patch("main.get_pending_letters", return_value=[]) as mock_gpl,
            patch("main.send_letter") as mock_send,
        ):
            poll(config)
        mock_send.assert_not_called()

    def test_successful_send_calls_mark_delivered_and_logs(self, tmp_path):
        config = self._config(tmp_path)
        letter_path = str(tmp_path / "letter.md")
        with (
            patch("main.get_pending_letters", return_value=[letter_path]),
            patch("main.send_letter") as mock_send,
            patch("main.mark_delivered") as mock_mark,
            patch("main.log_delivery") as mock_log,
        ):
            poll(config)

        mock_send.assert_called_once()
        mock_mark.assert_called_once()
        log_call = mock_log.call_args
        assert log_call[0][2] == "delivered"

    def test_failed_send_logs_failure_and_does_not_mark_delivered(self, tmp_path):
        config = self._config(tmp_path)
        letter_path = str(tmp_path / "letter.md")
        with (
            patch("main.get_pending_letters", return_value=[letter_path]),
            patch("main.send_letter", side_effect=Exception("SMTP error")),
            patch("main.mark_delivered") as mock_mark,
            patch("main.log_delivery") as mock_log,
        ):
            poll(config)

        mock_mark.assert_not_called()
        log_call = mock_log.call_args
        assert "failed" in log_call[0][2]
        assert "SMTP error" in log_call[0][2]

    def test_multiple_letters_all_processed(self, tmp_path):
        config = self._config(tmp_path)
        letters = [str(tmp_path / f"letter{i}.md") for i in range(3)]
        with (
            patch("main.get_pending_letters", return_value=letters),
            patch("main.send_letter"),
            patch("main.mark_delivered"),
            patch("main.log_delivery") as mock_log,
        ):
            poll(config)

        assert mock_log.call_count == 3

    def test_one_failure_does_not_stop_others(self, tmp_path):
        config = self._config(tmp_path)
        letters = [str(tmp_path / f"letter{i}.md") for i in range(2)]

        call_count = {"n": 0}

        def fail_first(path, cfg):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("first fails")

        with (
            patch("main.get_pending_letters", return_value=letters),
            patch("main.send_letter", side_effect=fail_first),
            patch("main.mark_delivered") as mock_mark,
            patch("main.log_delivery") as mock_log,
        ):
            poll(config)

        assert mock_mark.call_count == 1
        assert mock_log.call_count == 2
        statuses = [c[0][2] for c in mock_log.call_args_list]
        assert any("failed" in s for s in statuses)
        assert any(s == "delivered" for s in statuses)
