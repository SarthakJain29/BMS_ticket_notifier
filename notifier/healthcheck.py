"""Pings healthchecks.io after a successful check, so it can alert when checks stop."""

import os

from curl_cffi import requests


def ping() -> None:
    url = os.environ.get("HEALTHCHECK_URL")
    if not url:
        return
    try:
        requests.get(url, timeout=10)
    except requests.RequestsError as e:
        # Not fatal: healthchecks.io only alerts if pings keep missing
        print(f"Healthcheck ping failed: {e}")
