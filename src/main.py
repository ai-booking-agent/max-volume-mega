import datetime
import logging
import sys
import time

from . import config, discord_notify, spotify_playback_local, stats_scraper, whatsapp_notify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_DIR / "run.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("max-volume-mega")


def _wait_for_full_page(screenshot_path):
    """Phase 1: poll until every track on the recent-tracks page is from today.
    Returns the row keys present at that moment, or None if we gave up."""
    deadline = time.monotonic() + config.MAX_POLL_HOURS * 3600
    while time.monotonic() < deadline:
        log.info("Checking stats page (phase 1: filling with today's plays)...")
        try:
            done, today_count, total_count, row_keys = stats_scraper.check_and_screenshot(
                screenshot_path
            )
        except Exception:
            log.exception("Error while checking stats page, will retry")
            time.sleep(config.POLL_INTERVAL_SECONDS)
            continue

        log.info("%d/%d recent tracks are from today", today_count, total_count)
        if done:
            return row_keys

        time.sleep(config.POLL_INTERVAL_SECONDS)

    log.warning(
        "Gave up after %.1f hours without the recent-tracks page filling up with today's plays.",
        config.MAX_POLL_HOURS,
    )
    return None


def _wait_for_full_replacement(previous_keys, screenshot_path):
    """Phase 2: poll until every one of `previous_keys` has been pushed off the
    recent-tracks page by a newer same-day play. Returns True if detected."""
    deadline = time.monotonic() + config.MAX_POLL_HOURS * 3600
    while time.monotonic() < deadline:
        log.info("Checking stats page (phase 2: waiting for full turnover)...")
        try:
            done, current_keys = stats_scraper.check_full_replacement(
                previous_keys, screenshot_path
            )
        except Exception:
            log.exception("Error while checking stats page, will retry")
            time.sleep(config.POLL_INTERVAL_SECONDS)
            continue

        if done:
            return True

        time.sleep(config.POLL_INTERVAL_SECONDS)

    log.warning(
        "Gave up after %.1f hours waiting for the recent-tracks list to fully turn over.",
        config.MAX_POLL_HOURS,
    )
    return False


def run():
    log.info("Starting playback...")
    spotify_playback_local.start_playlist_playback()
    log.info("Playback started via local Spotify app")

    today = datetime.date.today().isoformat()
    date_text = datetime.date.today().strftime("%m/%d/%Y")
    screenshot_path_1 = config.SCREENSHOT_DIR / f"recent-tracks-{today}-1.png"
    screenshot_path_2 = config.SCREENSHOT_DIR / f"recent-tracks-{today}-2.png"

    phase1_keys = _wait_for_full_page(screenshot_path_1)
    if phase1_keys is None:
        return

    log.info("Recent-tracks page is full of today's plays.")
    caption_1 = f"🎵 Max Volume Mega — recent tracks all from today ({today})"

    try:
        log.info("Sending WhatsApp heads-up...")
        whatsapp_notify.send_screenshot(screenshot_path_1, date_text, caption_1)
        log.info("WhatsApp message sent.")
    except Exception:
        log.exception("Failed to send WhatsApp message, continuing to Discord prep")

    log.info("Prepping for Discord...")
    discord_notify.prepare_manual_send(screenshot_path_1, caption_1)
    log.info("Screenshot copied to clipboard and Discord channel opened.")

    log.info("Watching for the recent-tracks list to fully turn over...")
    if not _wait_for_full_replacement(phase1_keys, screenshot_path_2):
        return

    log.info("Recent-tracks list has fully turned over to new same-day plays.")
    caption_2 = f"🎵 Max Volume Mega — recent tracks list has fully refreshed today ({today})"

    try:
        log.info("Sending second WhatsApp update...")
        whatsapp_notify.send_screenshot(screenshot_path_2, date_text, caption_2)
        log.info("Second WhatsApp message sent.")
    except Exception:
        log.exception("Failed to send second WhatsApp message")

    log.info("Done.")


if __name__ == "__main__":
    run()
