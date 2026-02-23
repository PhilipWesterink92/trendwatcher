"""
Slack reporting module for sending trend insights.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .formatters import format_slack_blocks


def send_slack_report(
    trends_file: Path,
    channel: str,
    *,
    top_n: int = 10,
) -> bool:
    """
    Send trend report to Slack channel.

    Args:
        trends_file: Path to trends JSON file (analyzed or raw)
        channel: Slack channel (e.g., "#trendwatcher")
        top_n: Number of top trends to include

    Returns:
        True if successful

    Raises:
        ValueError: If Slack credentials not configured
        SlackApiError: If Slack API call fails
    """
    # Get Slack token from environment
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError(
            "SLACK_BOT_TOKEN not found. Please set it in your .env file. "
            "See docs/SETUP.md for instructions."
        )

    # Load trends
    if not trends_file.exists():
        raise FileNotFoundError(f"Trends file not found: {trends_file}")

    trends = json.loads(trends_file.read_text(encoding="utf-8"))

    # Initialize Slack client
    client = WebClient(token=token)

    # Format message as Slack blocks
    blocks = format_slack_blocks(trends, top_n=top_n)

    try:
        # Post message to channel
        response = client.chat_postMessage(
            channel=channel,
            blocks=blocks,
            text=f"Trendwatcher Report: Top {top_n} Trends",  # Fallback text
        )

        if response["ok"]:
            print(f"✓ Slack report sent to {channel}")
            return True
        else:
            raise SlackApiError(f"Slack API returned ok=False", response)

    except SlackApiError as e:
        print(f"✗ Slack error: {e.response['error']}")
        raise


def send_slack_message(
    channel: str,
    text: str,
    *,
    blocks: List[Dict[str, Any]] | None = None,
) -> bool:
    """
    Send a simple text message to Slack (utility function).

    Args:
        channel: Slack channel
        text: Message text (also used as fallback if blocks provided)
        blocks: Optional Slack blocks for rich formatting

    Returns:
        True if successful
    """
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN not found")

    client = WebClient(token=token)

    try:
        response = client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks,
        )
        return response["ok"]
    except SlackApiError as e:
        print(f"✗ Slack error: {e.response['error']}")
        raise
