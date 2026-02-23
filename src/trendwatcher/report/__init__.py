"""
Reporting module for sending trend insights via Slack and email.
"""
from .slack_reporter import send_slack_report
from .email_reporter import send_email_report

__all__ = ["send_slack_report", "send_email_report"]
