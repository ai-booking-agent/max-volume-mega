"""One-time interactive login to statsforspotify.com.

Run this once (and again if the site ever logs you out):

    python -m scripts.setup_stats_login

It opens a real, visible Chromium window using a persistent profile
directory. Log in with Spotify in that window. The script watches every open
tab and closes itself automatically once one of them lands on
statsforspotify.com (off of accounts.spotify.com / any /login path), saving
the session in .state/stats_browser_profile/ for headless reuse by the main
program.
"""
import time

from playwright.sync_api import sync_playwright

from src import config

TIMEOUT_SECONDS = 300


def _find_logged_in_page(context):
    for pg in context.pages:
        url = pg.url
        if (
            "statsforspotify.com" in url
            and "accounts.spotify.com" not in url
            and "/login" not in url
        ):
            return pg, url
    return None, None


def main():
    config.STATS_BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(config.STATS_BROWSER_PROFILE_DIR),
            headless=False,
        )
        page = context.new_page()
        page.goto(config.STATS_URL)
        print(
            "\nA browser window has opened. Log in to statsforspotify.com with "
            f"Spotify there (approve access). Waiting up to {TIMEOUT_SECONDS}s "
            "for you to land back on statsforspotify.com...\n",
            flush=True,
        )

        deadline = time.monotonic() + TIMEOUT_SECONDS
        last_report = 0
        found_page = None
        found_url = None
        while time.monotonic() < deadline:
            found_page, found_url = _find_logged_in_page(context)
            if found_page:
                break
            if time.monotonic() - last_report > 10:
                urls = [pg.url for pg in context.pages]
                print(f"[{int(time.monotonic())}] still waiting. open tabs: {urls}", flush=True)
                last_report = time.monotonic()
            time.sleep(2)

        if not found_page:
            urls = [pg.url for pg in context.pages]
            context.close()
            raise SystemExit(
                f"Timed out after {TIMEOUT_SECONDS}s waiting for login. "
                f"Open tabs were: {urls}. Run this again."
            )

        found_page.wait_for_timeout(2000)
        print(f"Detected login. Current URL: {found_page.url}", flush=True)
        context.close()
    print(f"Session saved to {config.STATS_BROWSER_PROFILE_DIR}", flush=True)


if __name__ == "__main__":
    main()
