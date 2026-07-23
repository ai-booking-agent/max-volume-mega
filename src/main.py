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


def run():
    log.info("Starting playback...")
    spotify_playback_local.start_playlist_playback()
    log.info("Playback started via local Spotify app")

    deadline = time.monotonic() + config.MAX_POLL_HOURS * 3600
    today = datetime.date.today().isoformat()
    screenshot_path = config.SCREENSHOT_DIR / f"recent-tracks-{today}.png"

    while time.monotonic() < deadline:
        log.info("Checking stats page...")
        try:
            done, today_count, total_count = stats_scraper.check_and_screenshot(screenshot_path)
        except Exception:
            log.exception("Error while checking stats page, will retry")
            time.sleep(config.POLL_INTERVAL_SECONDS)
            continue

        log.info("%d/%d recent tracks are from today", today_count, total_count)
        if done:
            log.info("Recent-tracks page is full of today's plays.")
            caption = f"🎵 Max Volume Mega — recent tracks all from today ({today})"
            date_text = datetime.date.today().strftime("%m/%d/%Y")

            try:
                log.info("Sending WhatsApp heads-up...")
                whatsapp_notify.send_screenshot(screenshot_path, date_text, caption)
                log.info("WhatsApp message sent.")
            except Exception:
                log.exception("Failed to send WhatsApp message, continuing to Discord prep")

            log.info("Prepping for Discord...")
            discord_notify.prepare_manual_send(screenshot_path, caption)
            log.info("Screenshot copied to clipboard and Discord channel opened. Done.")
            return

        time.sleep(config.POLL_INTERVAL_SECONDS)

    log.warning(
        "Gave up after %.1f hours without the recent-tracks page filling up with today's plays.",
        config.MAX_POLL_HOURS,
    )


if __name__ == "__main__":
    run()
