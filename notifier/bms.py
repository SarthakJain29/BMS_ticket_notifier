"""Fetches showtimes from BookMyShow's web API and turns them into shows."""

from dataclasses import dataclass

from curl_cffi import requests

from . import config

API_URL = "https://in.bookmyshow.com/api/movies-data/v5/showtimes-by-event/primary-dynamic"


class FetchError(Exception):
    pass


@dataclass(frozen=True)
class Show:
    venue_code: str
    starts: str  # YYYYMMDDHHMM
    time: str  # e.g. "08:15 AM"
    format: str  # e.g. "English 3D"
    session_id: str
    url: str

    @property
    def date(self) -> str:
        return self.starts[:8]

    @property
    def key(self) -> str:
        return f"{self.venue_code}|{self.date}|{self.session_id}"


def fetch_shows(date: str) -> list[Show]:
    """Returns all shows of the movie on `date`, across every format and venue."""
    params = {
        "etCodes": "*",  # all formats
        "refEventCode": config.EVENT_CODE,
        "language": config.LANGUAGE,
        "dateCode": date,
        "regionCode": config.REGION_CODE,
        "appCode": "WEB",
        "isDesktop": "true",
        "xLocationShared": "false",
        "memberId": "",
        "lsId": "",
        "subCode": "",
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "x-app-code": "WEB",
        "x-region-code": config.REGION_CODE,
        "x-region-slug": config.REGION_SLUG,
    }
    try:
        # impersonate makes the connection look like Chrome, which Cloudflare lets through
        resp = requests.get(API_URL, params=params, headers=headers, impersonate="chrome", timeout=20)
        resp.raise_for_status()
        data = resp.json()["data"]
        widgets = data["showtimeWidgets"]
    except (requests.RequestsError, ValueError, KeyError, TypeError) as e:
        raise FetchError(f"{date}: {type(e).__name__}: {e}") from e

    # If a date isn't open yet, BMS returns the nearest open date instead, so filter by show date.
    return [show for show in _parse(widgets) if show.date == date]


def _parse(widgets: list) -> list[Show]:
    shows = []
    for card in _venue_cards(widgets):
        venue_code = card["additionalData"]["venueCode"]
        url = _find_value(card, "redirectionUrl") or "https://in.bookmyshow.com"
        for section in card.get("showtimesSections", []):
            fmt = section.get("analytics", {}).get("format", "")
            for showtime in section.get("showtimes", []):
                info = showtime["additionalData"]
                shows.append(
                    Show(
                        venue_code=venue_code,
                        starts=info["showDateTime"],
                        time=info["showTime"],
                        format=" · ".join(filter(None, [fmt, info.get("attributes")])),
                        session_id=info["sessionId"],
                        url=url,
                    )
                )
    return shows


def _venue_cards(widgets: list):
    for widget in widgets:
        if widget.get("type") != "groupList":
            continue
        for group in widget.get("data", []):
            if group.get("type") != "venueGroup":
                continue
            for card in group.get("data", []):
                if card.get("type") == "venue-card":
                    yield card


def _find_value(obj, key: str):
    """Depth-first search for the first value stored under `key`."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        obj = list(obj.values())
    if isinstance(obj, list):
        for item in obj:
            if (found := _find_value(item, key)) is not None:
                return found
    return None
