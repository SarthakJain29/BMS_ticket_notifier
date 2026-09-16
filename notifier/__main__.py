"""Entry point: python -m notifier. Runs one check and exits."""

import os
from datetime import datetime, timedelta, timezone

from . import bms, config, healthcheck, notify
from .state import State, load, save

IST = timezone(timedelta(hours=5, minutes=30))


def main() -> None:
    now = datetime.now(IST).isoformat(timespec="seconds")
    shows, errors = fetch_watched_shows()
    for error in errors:
        print(f"Fetch failed: {error}")
    print(f"{len(shows)} shows at watched theatres, {len(errors)} failed dates")

    state = load(config.STATE_FILE)

    # Newly watched venues: record their current shows silently instead of alerting on all of them.
    # Skipped while any fetch fails, so a partial list can't cause false alerts later.
    new_venues = [code for code in config.VENUES if code not in state.venues]
    if new_venues and not errors:
        existing = [s for s in shows if s.venue_code in new_venues]
        record(state, existing, now)
        state.venues += new_venues
        notify.push("👀 Now watching", venue_counts_text(new_venues, [s.key for s in existing]))

    new_shows = [s for s in shows if s.venue_code in state.venues and s.key not in state.seen]
    if new_shows:
        alert_new_shows(new_shows)
        record(state, new_shows, now)

    if os.environ.get("HEARTBEAT") == "true":
        status = venue_counts_text(state.venues, state.seen)
        notify.push("💚 Notifier running", f"{status}\nLast check: {'failing' if errors else 'OK'}")

    save(state, config.STATE_FILE)

    # Only fully successful checks ping; healthchecks.io alerts when pings stop
    if not errors:
        healthcheck.ping()


def fetch_watched_shows() -> tuple[list[bms.Show], list[str]]:
    shows, errors = [], []
    for date in config.DATES:
        try:
            shows += [s for s in bms.fetch_shows(date) if s.venue_code in config.VENUES]
        except bms.FetchError as e:
            errors.append(str(e))
    return shows, errors


def record(state: State, shows: list[bms.Show], now: str) -> None:
    for show in shows:
        state.seen[show.key] = now


def alert_new_shows(shows: list[bms.Show]) -> None:
    shows = sorted(shows, key=lambda s: (s.venue_code, s.starts))
    venues = {s.venue_code for s in shows}
    title = f"🎟 {len(shows)} new show{'s' * (len(shows) > 1)} at "
    title += config.VENUES[shows[0].venue_code] if len(venues) == 1 else f"{len(venues)} theatres"

    lines, last_venue = [], None
    for show in shows:
        if show.venue_code != last_venue:
            lines.append(config.VENUES[show.venue_code])
            last_venue = show.venue_code
        lines.append(f"• {pretty_date(show.date)}, {show.time} · {show.format}")

    notify.push(title, "\n".join(lines), priority=notify.URGENT, click=shows[0].url, tags=["tickets"])


def venue_counts_text(venues: list[str], show_keys) -> str:
    """Shows per venue, from show keys ("VENUE|date|session")."""
    codes = [key.split("|")[0] for key in show_keys]
    lines = [f"{config.VENUES[code]}: {codes.count(code)} shows" for code in venues if code in config.VENUES]
    lines.append(f"Dates: {', '.join(pretty_date(d) for d in config.DATES)}")
    return "\n".join(lines)


def pretty_date(date: str) -> str:
    return datetime.strptime(date, "%Y%m%d").strftime("%a %d %b")


if __name__ == "__main__":
    main()
