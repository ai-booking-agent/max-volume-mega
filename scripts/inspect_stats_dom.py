"""Debug helper: dumps the logged-in statsforspotify recent-tracks page so we can
write correct scraper selectors. Not part of the daily automation.

    python -m scripts.inspect_stats_dom
"""
from playwright.sync_api import sync_playwright

from src import config

DEBUG_DIR = config.STATE_DIR / "debug"


def main():
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(config.STATS_BROWSER_PROFILE_DIR),
            headless=True,
        )
        page = context.new_page()
        page.goto(config.STATS_URL, wait_until="load", timeout=60000)
        page.wait_for_timeout(4000)

        (DEBUG_DIR / "page.html").write_text(page.content())
        page.screenshot(path=str(DEBUG_DIR / "page.png"), full_page=True)
        body_text = page.locator("body").inner_text()
        (DEBUG_DIR / "body_text.txt").write_text(body_text)

        print(f"Dumped HTML, screenshot, and text to {DEBUG_DIR}")
        print(f"Current URL after load: {page.url}")
        context.close()


if __name__ == "__main__":
    main()
