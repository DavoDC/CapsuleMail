"""Futuremail wrapper - sends a markdown file as an HTML email via SMTP."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import markdown


_SMTP_SETTINGS = {
    "outlook": {"host": "smtp-mail.outlook.com", "port": 587},
    "gmail":   {"host": "smtp.gmail.com",         "port": 587},
}


def _md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["extra"])


def _subject_from_file(filepath: str) -> str:
    name = Path(filepath).stem
    # Strip SEND-DATE suffix for a cleaner subject line
    import re
    name = re.sub(r"-SEND-\d{4}-\d{2}-\d{2}$", "", name)
    return name.replace("-", " ").title()


def send_letter(filepath: str, config: dict) -> None:
    """Send the markdown file at filepath as an HTML email.

    Raises on any SMTP or IO error - caller handles retry logic.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        body_md = f.read()

    # Strip any Status: header line before sending
    lines = body_md.splitlines()
    if lines and lines[0].startswith("Status:"):
        body_md = "\n".join(lines[1:]).lstrip()

    html_body = _md_to_html(body_md)
    subject = _subject_from_file(filepath)

    smtp_cfg = config["smtp"]
    provider = smtp_cfg.get("provider", "outlook")
    host_cfg = _SMTP_SETTINGS.get(provider, _SMTP_SETTINGS["outlook"])

    sender_email = smtp_cfg["email"]
    app_password = smtp_cfg["app_password"]

    recipients = [config["recipients"]["primary"]] + config["recipients"].get("alt", [])

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body_md, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(host_cfg["host"], host_cfg["port"]) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipients, msg.as_string())
