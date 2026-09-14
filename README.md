# BMS Ticket Notifier

Checks BookMyShow every 10 minutes and sends a push notification to your phone when new shows open at the theatres you care about.

Currently watching **Avengers Endgame: Encore** (all English formats) in Hyderabad at Prasads Multiplex, ALLU Cinemas Kokapet and AMB Cinemas Gachibowli, for 25–28 Sep.

## How it works

1. A GitHub Actions cron runs `python -m notifier`.
2. For each date, it calls BookMyShow's showtimes API once with `etCodes=*`, which returns every format of the movie.
3. It keeps shows at the watched venue codes and compares them with `state.json`.
4. New shows trigger an urgent [ntfy](https://ntfy.sh) push that opens the theatre's booking page.
5. `state.json` is committed back only when it changes.

Other notifications:
- **First run:** "Watching" push with the shows already open (they won't alert again).
- **Failures:** one alert if fetching keeps failing for 30 minutes, and another when it recovers.
- **Heartbeat:** daily at 09:00 IST, and on every manual run.

## Setup

1. Install the **ntfy** app and subscribe to a hard-to-guess topic name.
2. Add that topic as the `NTFY_TOPIC` repository secret (Settings → Secrets and variables → Actions).
3. Run the workflow once from the Actions tab. You should get the "Watching" push.

## Configuration

Edit [`notifier/config.py`](notifier/config.py): event code, language, region, dates and venue codes.

Venue codes appear in BookMyShow theatre URLs, e.g. `.../cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/...` → `PRHN`.

After changing theatres or the movie, delete `state.json` so the next run takes a fresh baseline.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m notifier                      # prints instead of pushing
NTFY_TOPIC=your-topic .venv/bin/python -m notifier  # real pushes
```

## Stop

Actions tab → **Check tickets** → **⋯** → **Disable workflow**.
