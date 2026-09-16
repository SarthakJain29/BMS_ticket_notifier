"""Sends push notifications through ntfy.sh."""

import os

from curl_cffi import requests

URGENT, DEFAULT = 5, 3


def push(title: str, message: str, priority: int = DEFAULT, click: str | None = None, tags: list[str] | None = None) -> None:
    """Pushes to the NTFY_TOPIC topic, or prints the notification when it isn't set."""
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print(f"[push skipped, NTFY_TOPIC not set]\n{title}\n{message}\n")
        return

    payload = {"topic": topic, "title": title, "message": message, "priority": priority}
    if click:
        payload["click"] = click
    if tags:
        payload["tags"] = tags
    resp = requests.post("https://ntfy.sh/", json=payload, timeout=15)
    resp.raise_for_status()
    print(f"Pushed: {title}")
