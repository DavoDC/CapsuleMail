"""Tests for sender.py - subject line logic and markdown rendering."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sender import _md_to_html, _subject_from_file, send_letter


class TestSubjectFromFile:
    def test_strips_send_date_suffix(self):
        assert _subject_from_file("futureme-letter-SEND-2027-05-10.md") == "Futureme Letter"

    def test_dashes_become_spaces_title_case(self):
        assert _subject_from_file("my-annual-reflection-SEND-2027-01-01.md") == "My Annual Reflection"

    def test_no_send_suffix_preserves_full_name(self):
        assert _subject_from_file("just-a-note.md") == "Just A Note"

    def test_single_word_filename(self):
        assert _subject_from_file("hello.md") == "Hello"

    def test_full_path_uses_stem_only(self):
        result = _subject_from_file("/some/dir/future-plans-SEND-2030-06-01.md")
        assert result == "Future Plans"

    def test_already_title_case_preserved(self):
        result = _subject_from_file("Dear-Future-Me-SEND-2028-12-25.md")
        assert result == "Dear Future Me"


class TestMdToHtml:
    def test_plain_text_returns_paragraph(self):
        html = _md_to_html("Hello world")
        assert "<p>Hello world</p>" in html

    def test_bold_renders_as_strong(self):
        html = _md_to_html("**bold**")
        assert "<strong>bold</strong>" in html

    def test_link_renders_as_anchor(self):
        html = _md_to_html("[click](https://example.com)")
        assert 'href="https://example.com"' in html
        assert ">click<" in html

    def test_output_is_html_string(self):
        html = _md_to_html("Some text")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_empty_string(self):
        html = _md_to_html("")
        assert isinstance(html, str)


class TestSendLetterStatusHeaderStrip:
    """Tests that send_letter strips the Status: header before sending."""

    def test_status_header_stripped_from_body(self, tmp_path):
        letter = tmp_path / "note-SEND-2026-05-10.md"
        letter.write_text(
            "Status: Delivered 2026-05-10 09:00:00\n\nDear Future Me,\n\nHello.\n"
        )
        config = {
            "smtp": {"provider": "outlook", "email": "a@b.com", "app_password": "x"},
            "recipients": {"primary": "a@b.com"},
        }

        captured_body = {}

        class FakeSMTP:
            def __init__(self, host, port):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def ehlo(self):
                pass
            def starttls(self, context=None):
                pass
            def login(self, user, pw):
                pass
            def sendmail(self, frm, to, msg_str):
                captured_body["msg"] = msg_str

        with patch("sender.smtplib.SMTP", FakeSMTP):
            send_letter(str(letter), config)

        assert "Status: Delivered" not in captured_body["msg"]
        assert "Dear Future Me" in captured_body["msg"]
