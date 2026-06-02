"""Tests for main.py - log_delivery (CSV I/O) and poll (core delivery loop)."""

import csv
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from main import log_delivery, poll, print_dashboard, send_with_retry


class TestSendWithRetry:
    def _cfg(self):
        return {"smtp": {}, "recipients": {"primary": "a@b.com"}}

    def test_succeeds_first_attempt_no_sleep(self):
        with (
            patch("main.send_letter") as mock_send,
            patch("main.time") as mock_time,
        ):
            send_with_retry("/letters/note.md", self._cfg())
        mock_send.assert_called_once()
        mock_time.sleep.assert_not_called()

    def test_retries_on_transient_failure_succeeds_second(self):
        calls = {"n": 0}

        def fail_once(path, cfg):
            calls["n"] += 1
            if calls["n"] == 1:
                raise Exception("transient")

        with (
            patch("main.send_letter", side_effect=fail_once),
            patch("main.time") as mock_time,
        ):
            send_with_retry("/letters/note.md", self._cfg())

        assert calls["n"] == 2
        mock_time.sleep.assert_called_once_with(10)

    def test_retries_twice_succeeds_third(self):
        calls = {"n": 0}

        def fail_twice(path, cfg):
            calls["n"] += 1
            if calls["n"] < 3:
                raise Exception("transient")

        with (
            patch("main.send_letter", side_effect=fail_twice),
            patch("main.time") as mock_time,
        ):
            send_with_retry("/letters/note.md", self._cfg())

        assert calls["n"] == 3
        sleep_calls = [c[0][0] for c in mock_time.sleep.call_args_list]
        assert sleep_calls == [10, 20]

    def test_raises_after_all_retries_fail(self):
        with (
            patch("main.send_letter", side_effect=Exception("permanent")),
            patch("main.time"),
        ):
            with pytest.raises(Exception, match="permanent"):
                send_with_retry("/letters/note.md", self._cfg())

    def test_sends_exactly_max_retries_times_on_all_fail(self):
        with (
            patch("main.send_letter", side_effect=Exception("fail")) as mock_send,
            patch("main.time"),
        ):
            with pytest.raises(Exception):
                send_with_retry("/letters/note.md", self._cfg())
        assert mock_send.call_count == 3


class TestPrintDashboard:
    def _config(self, tmp_path):
        return {
            "paths": {
                "letters_dir": str(tmp_path / "letters"),
                "logs_dir": str(tmp_path / "logs"),
            }
        }

    def test_shows_upcoming_letters(self, tmp_path, capsys):
        cfg = self._config(tmp_path)
        letters = tmp_path / "letters"
        letters.mkdir()
        future = date.today() + timedelta(days=3)
        (letters / f"dear-me-SEND-{future}.md").write_text("hello")

        print_dashboard(cfg)

        out = capsys.readouterr().out
        assert "Upcoming letters" in out
        assert str(future) in out
        assert "in 3d" in out

    def test_shows_today_label(self, tmp_path, capsys):
        cfg = self._config(tmp_path)
        letters = tmp_path / "letters"
        letters.mkdir()
        today = date.today()
        (letters / f"dear-me-SEND-{today}.md").write_text("hello")

        print_dashboard(cfg)

        assert "TODAY" in capsys.readouterr().out

    def test_shows_overdue_label(self, tmp_path, capsys):
        cfg = self._config(tmp_path)
        letters = tmp_path / "letters"
        letters.mkdir()
        past = date.today() - timedelta(days=2)
        (letters / f"dear-me-SEND-{past}.md").write_text("hello")

        print_dashboard(cfg)

        assert "overdue" in capsys.readouterr().out

    def test_no_letters_message(self, tmp_path, capsys):
        cfg = self._config(tmp_path)
        (tmp_path / "letters").mkdir()

        print_dashboard(cfg)

        assert "No upcoming letters." in capsys.readouterr().out

    def test_shows_recent_deliveries(self, tmp_path, capsys):
        cfg = self._config(tmp_path)
        (tmp_path / "letters").mkdir()
        logs = tmp_path / "logs"
        logs.mkdir()
        log_path = logs / "deliveries.csv"
        with open(log_path, "w", newline="") as f:
            import csv as csv_mod
            w = csv_mod.writer(f)
            w.writerow(["timestamp", "file", "status"])
            w.writerow(["2026-06-01 09:00:00", "letter.md", "delivered"])

        print_dashboard(cfg)

        out = capsys.readouterr().out
        assert "Recent deliveries" in out
        assert "letter.md" in out

    def test_no_crash_when_letters_dir_missing(self, tmp_path, capsys):
        cfg = self._config(tmp_path)
        print_dashboard(cfg)  # letters dir doesn't exist - should not raise


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
