# Max Volume Mega automation

Plays the [Max Volume Mega](https://open.spotify.com/playlist/1uu3OwGgJO4gfxZzGsXwDf) playlist
on your local Spotify desktop app and watches your statsforspotify.com recent-tracks page in two
stages:

1. Once every track listed is timestamped today, it screenshots the page, sends that screenshot to
   you on WhatsApp, then copies it to your clipboard and opens the target Discord channel so you
   can paste and send it yourself.
2. It keeps watching, and once every one of those original tracks has been pushed off the list by
   newer same-day plays (i.e. the whole list has turned over), it screenshots again and sends that
   second screenshot to you on WhatsApp too.

Runs daily, unattended, via launchd — except the Discord send after stage 1, which stays a manual
click.

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
   points at your target channel. For WhatsApp, see the dedicated section below.

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

## WhatsApp setup

Uses Meta's official WhatsApp Cloud API (not an unofficial/self-account automation — see
`src/whatsapp_notify.py` for why that route was avoided, same reasoning as the Discord section
above).

1. Create an app at [developers.facebook.com/apps](https://developers.facebook.com/apps) → type
   **Business** → add the **WhatsApp** product.
2. On **WhatsApp → API Setup**, copy the **Phone number ID**, add your own number under **To** and
   verify it, and send any WhatsApp message from your phone to that test number.
3. In [Business Settings → System Users](https://business.facebook.com/settings/system-users),
   create a System User (Admin), assign it the app *and* the WhatsApp Business Account (Business
   Settings → Accounts → WhatsApp Accounts) with Full control, then **Generate New Token** with
   `whatsapp_business_messaging` + `whatsapp_business_management` scopes, expiration **Never**.
4. Put the token, phone number ID, and your number (digits only, with country code, no `+`) into
   `.env` as `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_RECIPIENT_NUMBER`.
5. For the daily job to work without you texting the bot every 24 hours, create an approved
   message template in [WhatsApp Manager](https://business.facebook.com/wa/manage/message-templates/):
   name `max_volume_mega_screenshot`, category Utility, language English (US), an **Image** header,
   and a body with a `{{1}}` variable for the date. Once approved, sends use it automatically — the
   code tries the template first and falls back to a free-form message (which only works within 24h
   of you last texting the bot) if the template isn't approved yet.

## How it decides "done"

It polls statsforspotify's recent-tracks page every `POLL_INTERVAL_SECONDS` (default 5 min), each
stage getting up to `MAX_POLL_HOURS` (default 8h):

- **Stage 1** is done the moment every track currently listed is timestamped today — i.e. the
  whole recent-tracks list has been pushed to today's plays.
- **Stage 2** is done once every one of the specific plays present at stage 1 has disappeared from
  the list (replaced by newer same-day plays) — i.e. the list has fully turned over since then.

## Logs

- `logs/run.log` — application log
- `logs/launchd.out.log` / `logs/launchd.err.log` — stdout/stderr from the scheduled job

## Re-running setup

- If statsforspotify logs you out, re-run `scripts/setup_stats_login`.
