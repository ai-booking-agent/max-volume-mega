import subprocess

from . import config

_APPLESCRIPT = '''
tell application "Spotify"
    activate
    play track "spotify:playlist:{playlist_id}"
end tell
'''


def start_playlist_playback(playlist_id=None):
    """Starts playback of the playlist in the local Spotify desktop app via
    AppleScript. Works on free accounts (it's the same as clicking play in the
    app) — no Spotify Web API playback call, no Premium requirement.

    Requires: Spotify desktop app installed and you logged in on this Mac, and
    macOS Automation permission granted for the terminal/Python to control
    Spotify (macOS will prompt for this the first time).
    """
    playlist_id = playlist_id or config.SPOTIFY_PLAYLIST_ID
    script = _APPLESCRIPT.format(playlist_id=playlist_id)
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript playback failed: {result.stderr.strip()}")
