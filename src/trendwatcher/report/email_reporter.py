"""
Email reporting module for sending trend insights.
"""
from __future__ import annotations

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List

from .formatters import format_email_html


def send_email_report(
    trends_file: Path,
    recipients: List[str],
    *,
    top_n: int = 25,
    subject: str | None = None,
) -> bool:
    """
    Send trend report via email.

    Args:
        trends_file: Path to trends JSON file
        recipients: List of email addresses
        top_n: Number of top trends to include
        subject: Optional custom subject line

    Returns:
        True if successful

    Raises:
        ValueError: If email credentials not configured
    """
    # Get SMTP configuration from environment
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_user)

    if not smtp_user or not smtp_password:
        raise ValueError(
            "SMTP credentials not found. Please set SMTP_USER and SMTP_PASSWORD "
            "in your .env file. See docs/SETUP.md for instructions."
        )

    # Load trends
    if not trends_file.exists():
        raise FileNotFoundError(f"Trends file not found: {trends_file}")

    trends = json.loads(trends_file.read_text(encoding="utf-8"))

    # Create email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject or f"🔥 Trendwatcher Report: Top {top_n} Trends"
    msg["From"] = from_email
    msg["To"] = ", ".join(recipients)

    # Plain text version (simple fallback)
    text_body = f"Trendwatcher Report\n\nTop {top_n} food trends:\n\n"
    for i, trend in enumerate(trends[:top_n], start=1):
        trend_name = trend.get("trend", "Unknown")
        score = trend.get("score", 0)
        text_body += f"{i}. {trend_name} (Score: {score})\n"

    # HTML version (rich formatting)
    html_body = format_email_html(trends, top_n=top_n)

    # Attach both versions
    part1 = MIMEText(text_body, "plain")
    part2 = MIMEText(html_body, "html")
    msg.attach(part1)
    msg.attach(part2)

    # Send email
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Upgrade to secure connection
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, recipients, msg.as_string())

        print(f"✓ Email report sent to {len(recipients)} recipient(s)")
        return True

    except Exception as e:
        print(f"✗ Email error: {e}")
        raise


def send_test_email(recipient: str) -> bool:
    """
    Send a test email to verify SMTP configuration.

    Args:
        recipient: Email address to send test to

    Returns:
        True if successful
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_user)

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP credentials not found")

    msg = MIMEText("This is a test email from Trendwatcher. If you received this, your email configuration is working!")
    msg["Subject"] = "Trendwatcher Test Email"
    msg["From"] = from_email
    msg["To"] = recipient

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, [recipient], msg.as_string())

        print(f"✓ Test email sent to {recipient}")
        return True

    except Exception as e:
        print(f"✗ Test email failed: {e}")
        raise
