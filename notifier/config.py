"""What to watch. Edit these values to track another movie, city, dates or theatres."""

# Any format's event code works; the API is queried for all formats of the movie.
EVENT_CODE = "ET00514163"  # Avengers Endgame: Encore (English 2D)
LANGUAGE = "english"

REGION_CODE = "HYD"
REGION_SLUG = "hyderabad"

DATES = ["20260925", "20260926", "20260927", "20260928"]  # YYYYMMDD

# BookMyShow venue code -> name used in notifications
VENUES = {
    "PRHN": "Prasads Multiplex",
    "ALUC": "ALLU Cinemas Kokapet",
    "AMBH": "AMB Cinemas Gachibowli",
}

STATE_FILE = "state.json"

# Alert only if fetching keeps failing this long (avoids noise from one-off errors)
FAILURE_ALERT_AFTER_MINUTES = 30
