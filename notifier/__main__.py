"""Entry point: python -m notifier. Runs one check and exits."""

import os
import sys
from datetime import datetime, timedelta, timezone

from . import bms, config, notify
from .state import State, load, save

IST = timezone(timedelta(hours=5, minutes=30))


def main() -> None:
    now = datetime.now(IST)
    shows, errors = fetch_watched_shows()
    for error in errors:
        print(f"Fetch failed: {error}")
    print(f"{len(shows)} shows at watched theatres, {len(errors)} failed dates")

    state = load(config.STATE_FILE)
    if state is None:
        if errors:
            sys.exit("First run failed to fetch every date; not saving a partial baseline.")
        state = State()
        record(state, shows, now)
        notify.push("👀 Watching for new shows", status_text(state), click=shows[0].url if shows else None)
        save(state, config.STATE_FILE)
        return

    new_shows = [show for show in shows if show.key not in state.seen]
    if new_shows:
        alert_new_shows(new_shows)
        record(state, new_shows, now)

    track_failures(state, errors, now)

    if os.environ.get("HEARTBEAT") == "true":
        notify.push("💚 Notifier running", status_text(state, errors))

    save(state, config.STATE_FILE)


def fetch_watched_shows() -> tuple[list[bms.Show], list[str]]:
    shows, errors = [], []
    for date in config.DATES:
        try:
            shows += [s for s in bms.fetch_shows(date) if s.venue_code in config.VENUES]
        except bms.FetchError as e:
            errors.append(str(e))
    return shows, errors


def record(state: State, shows: list[bms.Show], now: datetime) -> None:
    for show in shows:
        state.seen[show.key] = now.isoformat(timespec="seconds")


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


def track_failures(state: State, errors: list[str], now: datetime) -> None:
    if not errors:
        if state.failure_alerted:
            notify.push("✅ Notifier recovered", "Fetching from BookMyShow works again.")
        state.failing_since, state.failure_alerted = None, False
        return

    if state.failing_since is None:
        state.failing_since = now.isoformat(timespec="seconds")
    failing_for = now - datetime.fromisoformat(state.failing_since)
    if not state.failure_alerted and failing_for >= timedelta(minutes=config.FAILURE_ALERT_AFTER_MINUTES):
        minutes = int(failing_for.total_seconds() // 60)
        notify.push(f"⚠️ Notifier failing for {minutes} min", "\n".join(errors), priority=notify.HIGH)
        state.failure_alerted = True


def status_text(state: State, errors: list[str] | None = None) -> str:
    counts = {code: 0 for code in config.VENUES}
    for key in state.seen:
        code = key.split("|")[0]
        if code in counts:
            counts[code] += 1
    lines = [f"{config.VENUES[code]}: {count} shows" for code, count in counts.items()]
    lines.append(f"Dates: {', '.join(pretty_date(d) for d in config.DATES)}")
    lines.append(f"Last check: {'failing' if errors else 'OK'}")
    return "\n".join(lines)


def pretty_date(date: str) -> str:
    return datetime.strptime(date, "%Y%m%d").strftime("%a %d %b")


if __name__ == "__main__":
    main()
