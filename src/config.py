import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT_DIR / ".state"
LOG_DIR = ROOT_DIR / "logs"
STATE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

load_dotenv(ROOT_DIR / ".env")

# Playback is driven locally via AppleScript against the Spotify desktop app —
# no Spotify API credentials, no user login, no Premium requirement needed.
# See spotify_playback_local.py.
SPOTIFY_PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID", "1uu3OwGgJO4gfxZzGsXwDf")

# No posting automation — we only copy the screenshot to the clipboard and
# open this channel so you can paste and send it yourself (see discord_notify.py).
DISCORD_CHANNEL_URL = os.environ.get(
    "DISCORD_CHANNEL_URL",
    "https://discord.com/channels/1173706955852873818/1206527185964236830",
)

STATS_URL = os.environ.get("STATS_URL", "https://www.statsforspotify.com/track/recent")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))
MAX_POLL_HOURS = float(os.environ.get("MAX_POLL_HOURS", "8"))

STATS_BROWSER_PROFILE_DIR = STATE_DIR / "stats_browser_profile"
SCREENSHOT_DIR = STATE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)
