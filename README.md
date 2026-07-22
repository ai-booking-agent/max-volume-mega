# Max Volume Mega automation

Plays the [Max Volume Mega](https://open.spotify.com/playlist/1uu3OwGgJO4gfxZzGsXwDf) playlist
on your local Spotify desktop app, waits until every track on your statsforspotify.com
recent-tracks page is timestamped today, screenshots that page, copies it to your clipboard, and
opens the target Discord channel so you can paste and send it yourself. Runs daily, unattended,
via launchd — except the final send, which stays a manual click.

Playback is driven locally via AppleScript against the Spotify desktop app — the same as clicking
play yourself — so it works on a **free Spotify account** with **no Spotify API credentials at
all**. (Spotify's own free-tier restrictions, like ads or forced shuffle on playlists you don't
own, still apply — that's Spotify's product behavior, not something a script can change.)

The Discord step is deliberately manual: you don't have Manage Webhooks/bot permissions on that
channel, and automating a personal Discord account to send messages (whether via the API or by
scripting a browser) violates Discord's Terms of Service. So the script does everything up to the
send — screenshot copied to your clipboard, channel opened — and you press Cmd+V and Enter.

## One-time setup

1. **Install dependencies** (already done if you're reading this after the initial build):
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Fill in `.env`** (copy from `.env.example`) — the default `DISCORD_CHANNEL_URL` already
   points at your target channel, so this step is optional unless you want to change it.

3. **Log in to statsforspotify.com** (opens a real browser window once, session persists after):
   ```
   python -m scripts.setup_stats_login
   ```

4. **Make sure Spotify desktop app is installed and you're logged in** on this Mac. The first
   time the automation runs, macOS will prompt you to allow Terminal/Python to control Spotify via
   Automation — approve it (System Settings → Privacy & Security → Automation).

5. **Test one run manually** before scheduling it:
   ```
   python -m src.main
   ```

6. **Schedule the daily unattended run**:
   ```
   python -m scripts.install_scheduler --hour 9 --minute 0
   ```
   Installs a launchd agent that fires once a day. Your Mac needs to be awake and the Spotify app
   needs to be installed at that time (the AppleScript `activate` call will launch it if it's not
   already running).

## How it decides "done for the day"

It polls statsforspotify's recent-tracks page every `POLL_INTERVAL_SECONDS` (default 5 min) for
up to `MAX_POLL_HOURS` (default 8h). It's "done" the moment every track currently listed on that
page is timestamped today — i.e. the whole recent-tracks list has been pushed to today's plays.

## Logs

- `logs/run.log` — application log
- `logs/launchd.out.log` / `logs/launchd.err.log` — stdout/stderr from the scheduled job

## Re-running setup

- If statsforspotify logs you out, re-run `scripts/setup_stats_login`.
