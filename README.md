# BMS Ticket Notifier

Checks BookMyShow every 10 minutes and sends a push notification to your phone when new shows open at the theatres you care about.

Currently watching **Avengers Endgame: Encore** (all English formats) in Hyderabad at Prasads Multiplex, ALLU Cinemas Kokapet, AMB Cinemas Gachibowli and PVR Superplex Inorbit, for 25–28 Sep.

## How it works

1. [cron-job.org](https://cron-job.org) calls GitHub's API every 10 minutes to start the **Check tickets** workflow. GitHub's own schedule stays as a backup, since it often skips runs.
2. The workflow runs `python -m notifier`. For each date it calls BookMyShow's showtimes API once with `etCodes=*`, which returns every format.
3. It keeps shows at the watched venue codes and compares them with `state.json`.
4. New shows trigger an urgent [ntfy](https://ntfy.sh) push that opens the theatre's booking page.
5. `state.json` is committed back only when it changes.
6. Each fully successful check pings [healthchecks.io](https://healthchecks.io), which alerts you if checks stop or keep failing.

Other notifications:
- **Newly added theatre (and the first run):** a "Now watching" push with the shows already open. Those shows won't alert again.
- **Heartbeat:** daily at 09:00 IST, or on a manual run with **Send a 💚 status push** ticked.

## Setup

1. **ntfy:** install the app and subscribe to a hard-to-guess topic.
2. **Repository secrets** (Settings → Secrets and variables → Actions):
   - `NTFY_TOPIC`: the topic name
   - `HEALTHCHECK_URL`: the check's ping URL from healthchecks.io
3. **healthchecks.io:** create a check with period 10 minutes and grace 20 minutes, and add the ntfy integration.
4. **cron-job.org:** every 10 minutes, `POST` to `https://api.github.com/repos/<owner>/<repo>/actions/workflows/check.yml/dispatches` with:
   - Body: `{"ref":"main"}`
   - Headers:
     - `Authorization: Bearer <token>`: a fine-grained token with **Actions: read and write** on this repo only
     - `Accept: application/vnd.github+json`
     - `X-GitHub-Api-Version: 2022-11-28`

## Configuration

Edit [`notifier/config.py`](notifier/config.py): event code, language, region, dates and venue codes.

Venue codes appear in BookMyShow theatre URLs, e.g. `.../cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/...` → `PRHN`. New theatres are baselined automatically. When switching to another movie, delete `state.json`.

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m notifier                        # prints instead of pushing
NTFY_TOPIC=your-topic .venv/bin/python -m notifier  # real pushes
```

## Stop

1. Disable the cron-job.org job.
2. Actions tab → **Check tickets** → **⋯** → **Disable workflow**.
3. Pause the check on healthchecks.io.
