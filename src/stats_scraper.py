import datetime

from playwright.sync_api import sync_playwright

from . import config

ROW_SELECTOR = "li.track-row"
TITLE_SELECTOR = ".track-name"
ARTIST_SELECTOR = ".artist-name"
PLAYED_AT_SELECTOR = ".played-at"


def open_context(playwright, headless=True):
    config.STATS_BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        str(config.STATS_BROWSER_PROFILE_DIR),
        headless=headless,
    )
    return context


def goto_recent(page):
    page.goto(config.STATS_URL, wait_until="load", timeout=60000)
    page.wait_for_timeout(4000)
    if page.locator("text=Something went wrong").count() > 0:
        page.reload(wait_until="load", timeout=60000)
        page.wait_for_timeout(4000)


def _parse_played_at(text):
    # e.g. "07/21/2026, 08:08 PM"
    date_part = text.split(",")[0].strip()
    return datetime.datetime.strptime(date_part, "%m/%d/%Y").date()


def extract_recent_tracks(page):
    """Returns a list of {title, artist, time_text, is_today} for each row on the
    recent-tracks page, most recent first, in the order they appear on the page.

    Selectors confirmed against the live DOM via scripts/inspect_stats_dom.py:
    rows are `li.track-row`, with `.track-name`, `.artist-name`, and
    `.played-at` (format "MM/DD/YYYY, HH:MM PM") inside each.
    """
    today = datetime.date.today()
    rows = []
    for row in page.locator(ROW_SELECTOR).all():
        title = row.locator(TITLE_SELECTOR).inner_text().strip()
        artist = row.locator(ARTIST_SELECTOR).inner_text().strip()
        time_text = row.locator(PLAYED_AT_SELECTOR).inner_text().strip()
        try:
            is_today = _parse_played_at(time_text) == today
        except ValueError:
            is_today = False
        rows.append(
            {"title": title, "artist": artist, "time_text": time_text, "is_today": is_today}
        )
    return rows


def screenshot_full_page(page, path):
    page.screenshot(path=str(path), full_page=True)
    return path


def check_and_screenshot(screenshot_path):
    """Opens the stats page and checks whether every track currently listed is
    timestamped today (i.e. the whole recent-tracks list has been pushed to
    today's plays). Returns (done: bool, today_count: int, total_count: int).
    """
    with sync_playwright() as p:
        context = open_context(p, headless=True)
        try:
            page = context.new_page()
            goto_recent(page)
            rows = extract_recent_tracks(page)

            today_count = sum(1 for r in rows if r["is_today"])
            done = len(rows) > 0 and today_count == len(rows)
            if done:
                screenshot_full_page(page, screenshot_path)
            return done, today_count, len(rows)
        finally:
            context.close()
