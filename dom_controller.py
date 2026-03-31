"""
Jarvis Assistant - DOM Controller
DOM-based browser automation for YouTube, YouTube Music, and Spotify Web.
Uses Playwright to open pages and inject/execute JavaScript (or native clicks)
to select and play the first result. No screen coordinates or tab guessing.
"""

import os
import time
from urllib.parse import quote
from typing import Optional, Any

import config

# Optional: Playwright for DOM automation. If not installed, DOM methods return False.
_dom_available: Optional[bool] = None


def _dom_available_check() -> bool:
    """True if Playwright is importable (for is_dom_available)."""
    global _dom_available
    if _dom_available is not None:
        return _dom_available
    try:
        from playwright.sync_api import sync_playwright
        _dom_available = True
    except Exception:
        _dom_available = False
    return _dom_available


def _log(msg: str) -> None:
    try:
        from debug_log import log as _log_fn
        _log_fn(msg)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# YouTube Music - DOM first
# ---------------------------------------------------------------------------
# Selectors for first playable result (may need tuning if YT Music updates UI).
# Try play button first, then first row/link.
YT_MUSIC_FIRST_RESULT_SELECTORS = [
    "ytmusic-responsive-list-item-renderer #play-button",  # Play button in first row
    "ytmusic-responsive-list-item-renderer .middle-column",  # Click row to select
    "ytmusic-responsive-list-item-renderer a",               # Link in first row
    "ytmusic-responsive-list-item-renderer",                 # First list item (song row)
    "ytmusic-shelf-renderer ytmusic-responsive-list-item-renderer",
    "ytd-video-renderer a#video-title",
]


def _get_chrome_user_data_dir() -> str:
    """Profile dir for YT Music so you stay signed in. Uses config or default Jarvis folder."""
    if getattr(config, "CHROME_USER_DATA_DIR", None):
        return config.CHROME_USER_DATA_DIR.strip()
    local = os.environ.get("LOCALAPPDATA", "")
    return os.path.join(local, "Jarvis", "ChromeProfile")


def play_youtube_music(song_name: str, headless: bool = False) -> bool:
    """
    DOM automation for YouTube Music: open search URL in a persistent Chrome
    profile (so you stay signed in), large window, wait for results, click
    first result and press Space to start playback.
    """
    if not _dom_available_check():
        _log("dom_controller: Playwright not available, DOM skipped")
        return False
    song_plus = song_name.replace(" ", "+")
    url = "https://music.youtube.com/search?q=" + song_plus
    # So Google/YouTube allows sign-in: don't advertise automation (ignore_default_args + disable-blink-features)
    # Enable CDP so we can reattach to this same browser on later requests and search/play in the same tab.
    port = getattr(config, "CHROME_DEBUGGING_PORT", 9222)
    use_large_viewport = getattr(config, "USE_LARGE_VIEWPORT_INSTEAD_OF_MAXIMIZED", False)
    viewport = None
    args = ["--disable-blink-features=AutomationControlled", f"--remote-debugging-port={port}"]
    if not headless:
        if not use_large_viewport:
            args.append("--start-maximized")
        else:
            viewport = {
                "width": getattr(config, "VIEWPORT_WIDTH", 1920),
                "height": getattr(config, "VIEWPORT_HEIGHT", 1080),
            }
    user_data_dir = _get_chrome_user_data_dir()
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        try:
            # Persistent context = same profile every time (sign in once to YT Music)
            # ignore_default_args: don't add --enable-automation so sign-in works
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                channel="chrome" if not headless else None,
                headless=headless,
                viewport=viewport,
                args=args,
                ignore_default_args=["--enable-automation"],
            )
        except TypeError:
            # Older Playwright may not support ignore_default_args
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                channel="chrome" if not headless else None,
                headless=headless,
                viewport=viewport,
                args=args,
            )
        except Exception:
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=headless,
                viewport=viewport or {"width": 1920, "height": 1080},
                args=["--disable-blink-features=AutomationControlled"],
            )
        page = context.pages[0] if context.pages else context.new_page()
        _log("dom_controller: navigating to YT Music search")
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_load_state("networkidle", timeout=18000)
        time.sleep(4.0)
        clicked = False
        for selector in YT_MUSIC_FIRST_RESULT_SELECTORS:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    el.wait_for(state="visible", timeout=6000)
                    el.click()
                    _log(f"dom_controller: clicked first result (selector: {selector})")
                    clicked = True
                    break
            except Exception as e:
                _log(f"dom_controller: selector {selector} failed: {e}")
                continue
        if not clicked:
            js_click = """
            () => {
                var btn = document.querySelector('ytmusic-responsive-list-item-renderer #play-button');
                if (btn) { btn.click(); return true; }
                var row = document.querySelector('ytmusic-responsive-list-item-renderer');
                if (row) { row.click(); return true; }
                var a = document.querySelector('ytmusic-responsive-list-item-renderer a') ||
                        document.querySelector('ytd-video-renderer a#video-title');
                if (a) { a.click(); return true; }
                return false;
            }
            """
            try:
                clicked = page.evaluate(js_click)
                if clicked:
                    _log("dom_controller: clicked first result via JS")
            except Exception as e:
                _log(f"dom_controller: JS click failed: {e}")
        if clicked:
            time.sleep(0.5)
            page.keyboard.press("Space")
            _log("dom_controller: Space to ensure playback")
        # Leave browser open so playback continues and you stay signed in
        return clicked
    except Exception as e:
        _log(f"dom_controller: play_youtube_music failed: {e}")
        return False


def click_first_yt_music_result_on_page(page: Any) -> bool:
    """
    Given a Playwright page already on YT Music (e.g. search results),
    wait for results, find and click the first playable result, press Space.
    Returns True if a click was performed.
    """
    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(2.0)
        clicked = False
        for selector in YT_MUSIC_FIRST_RESULT_SELECTORS:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    el.wait_for(state="visible", timeout=6000)
                    el.click()
                    _log(f"dom_controller: clicked first result (selector: {selector})")
                    clicked = True
                    break
            except Exception as e:
                _log(f"dom_controller: selector {selector} failed: {e}")
                continue
        if not clicked:
            js_click = """
            () => {
                var btn = document.querySelector('ytmusic-responsive-list-item-renderer #play-button');
                if (btn) { btn.click(); return true; }
                var row = document.querySelector('ytmusic-responsive-list-item-renderer');
                if (row) { row.click(); return true; }
                var a = document.querySelector('ytmusic-responsive-list-item-renderer a') ||
                        document.querySelector('ytd-video-renderer a#video-title');
                if (a) { a.click(); return true; }
                return false;
            }
            """
            try:
                clicked = page.evaluate(js_click)
                if clicked:
                    _log("dom_controller: clicked first result via JS")
            except Exception as e:
                _log(f"dom_controller: JS click failed: {e}")
        if clicked:
            time.sleep(0.5)
            page.keyboard.press("Space")
            _log("dom_controller: Space to ensure playback")
        return clicked
    except Exception as e:
        _log(f"dom_controller: click_first_yt_music_result_on_page failed: {e}")
        return False


def click_first_spotify_result_on_page(page: Any) -> bool:
    """
    Given a Playwright page already on Spotify Web (e.g. search results),
    find and click the first track / play button. Returns True if a click was performed.
    """
    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(2.0)
        clicked = False
        for selector in [SPOTIFY_PLAY_BUTTON, SPOTIFY_FIRST_TRACK_ROW]:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    el.wait_for(state="visible", timeout=6000)
                    el.click()
                    _log(f"dom_controller: clicked Spotify first result (selector: {selector})")
                    clicked = True
                    break
            except Exception as e:
                _log(f"dom_controller: Spotify selector {selector} failed: {e}")
                continue
        if not clicked:
            try:
                clicked = page.evaluate("""() => {
                    const btn = document.querySelector("button[data-testid='play-button']");
                    const row = document.querySelector("div[data-testid='tracklist-row']");
                    if (btn) { btn.click(); return true; }
                    if (row) { row.click(); return true; }
                    return false;
                }""")
                if clicked:
                    _log("dom_controller: clicked Spotify first result via JS")
            except Exception:
                pass
        return clicked
    except Exception as e:
        _log(f"dom_controller: click_first_spotify_result_on_page failed: {e}")
        return False


def try_click_yt_music_via_cdp(wait_sec: float = 2.0) -> bool:
    """
    Try to connect to Chrome via CDP (remote-debugging-port), find a page on
    music.youtube.com, and run DOM click on first result. Use when the user
    has already navigated to YT Music search in their tab.
    Returns True if connection and click succeeded. Requires Chrome to be
    launched with --remote-debugging-port=9222 (see config.CHROME_DEBUGGING_PORT).
    """
    if not _dom_available_check():
        return False
    port = getattr(config, "CHROME_DEBUGGING_PORT", 9222)
    cdp_url = f"http://127.0.0.1:{port}"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=8000)
            try:
                time.sleep(wait_sec)
                for context in browser.contexts:
                    for page in context.pages:
                        url = (page.url or "").lower()
                        if "music.youtube.com" in url:
                            _log("dom_controller: found YT Music page via CDP, clicking first result")
                            return click_first_yt_music_result_on_page(page)
            finally:
                browser.close()
        return False
    except Exception as e:
        _log(f"dom_controller: try_click_yt_music_via_cdp failed: {e}")
        return False


def navigate_yt_music_tab_and_play_via_cdp(song_name: str) -> bool:
    """
    Connect via CDP, find the tab that has music.youtube.com, bring that tab to front,
    navigate it to the search URL for song_name, then run DOM click on first result.
    So the search and play happen inside the existing YT Music tab only (no new tab).
    Returns True if connection, navigation and click succeeded.
    """
    if not _dom_available_check():
        return False
    song_plus = song_name.replace(" ", "+")
    search_url = "https://music.youtube.com/search?q=" + song_plus
    port = getattr(config, "CHROME_DEBUGGING_PORT", 9222)
    cdp_url = f"http://127.0.0.1:{port}"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=8000)
            try:
                for context in browser.contexts:
                    for page in context.pages:
                        url = (page.url or "").lower()
                        if "music.youtube.com" in url:
                            _log("dom_controller: found YT Music tab, bringing to front and navigating")
                            page.bring_to_front()
                            page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
                            page.wait_for_load_state("networkidle", timeout=18000)
                            time.sleep(2.0)
                            return click_first_yt_music_result_on_page(page)
            finally:
                browser.close()
        return False
    except Exception as e:
        _log(f"dom_controller: navigate_yt_music_tab_and_play_via_cdp failed: {e}")
        return False


def navigate_spotify_tab_and_play_via_cdp(song_name: str) -> bool:
    """
    Connect via CDP, find the tab that has open.spotify.com, bring it to front,
    navigate to search URL, then run DOM click on first result. Same-tab only.
    """
    if not _dom_available_check():
        return False
    song_encoded = quote(song_name)
    search_url = config.SPOTIFY_WEB_URL + song_encoded
    port = getattr(config, "CHROME_DEBUGGING_PORT", 9222)
    cdp_url = f"http://127.0.0.1:{port}"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=8000)
            try:
                for context in browser.contexts:
                    for page in context.pages:
                        url = (page.url or "").lower()
                        if "open.spotify.com" in url:
                            _log("dom_controller: found Spotify tab, bringing to front and navigating")
                            page.bring_to_front()
                            page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
                            page.wait_for_load_state("networkidle", timeout=18000)
                            time.sleep(2.0)
                            return click_first_spotify_result_on_page(page)
            finally:
                browser.close()
        return False
    except Exception as e:
        _log(f"dom_controller: navigate_spotify_tab_and_play_via_cdp failed: {e}")
        return False


def try_click_spotify_via_cdp(wait_sec: float = 2.0) -> bool:
    """
    Try to connect to Chrome via CDP, find a page on open.spotify.com,
    and run DOM click on first result. Returns True if connection and click succeeded.
    """
    if not _dom_available_check():
        return False
    port = getattr(config, "CHROME_DEBUGGING_PORT", 9222)
    cdp_url = f"http://127.0.0.1:{port}"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url, timeout=8000)
            try:
                time.sleep(wait_sec)
                for context in browser.contexts:
                    for page in context.pages:
                        url = (page.url or "").lower()
                        if "open.spotify.com" in url:
                            _log("dom_controller: found Spotify page via CDP, clicking first result")
                            return click_first_spotify_result_on_page(page)
            finally:
                browser.close()
        return False
    except Exception as e:
        _log(f"dom_controller: try_click_spotify_via_cdp failed: {e}")
        return False


# ---------------------------------------------------------------------------
# YouTube (youtube.com/results) - DOM first
# ---------------------------------------------------------------------------
YT_FIRST_RESULT_SELECTORS = [
    "ytd-video-renderer a#video-title",
    "ytd-video-renderer a#title",
]


def play_youtube(song_name: str, headless: bool = False) -> bool:
    """
    DOM automation for YouTube (youtube.com/results): open search URL,
    click the first video result via DOM (e.g. ytd-video-renderer a#video-title).
    """
    if not _dom_available_check():
        return False
    song_plus = song_name.replace(" ", "+")
    url = "https://www.youtube.com/results?search_query=" + song_plus
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=headless)
            except Exception:
                browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            _log("dom_controller: navigating to YouTube search")
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2.0)
            clicked = False
            for selector in YT_FIRST_RESULT_SELECTORS:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        el.wait_for(state="visible", timeout=5000)
                        el.click()
                        _log(f"dom_controller: clicked first YT result (selector: {selector})")
                        clicked = True
                        break
                except Exception as e:
                    _log(f"dom_controller: YT selector {selector} failed: {e}")
                    continue
            if not clicked:
                try:
                    clicked = page.evaluate("""() => {
                        const a = document.querySelector("ytd-video-renderer a#video-title");
                        if (a) { a.click(); return true; }
                        return false;
                    }""")
                    if clicked:
                        _log("dom_controller: clicked first YT result via JS")
                except Exception:
                    pass
            browser.close()
        return clicked
    except Exception as e:
        _log(f"dom_controller: play_youtube failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Spotify Web - DOM first
# ---------------------------------------------------------------------------
# Spotify Web uses data-testid: search-input, tracklist-row, play-button.
SPOTIFY_SEARCH_INPUT = "input[data-testid='search-input']"
SPOTIFY_FIRST_TRACK_ROW = "div[data-testid='tracklist-row']"
SPOTIFY_PLAY_BUTTON = "button[data-testid='play-button']"


def play_spotify_web(song_name: str, headless: bool = False) -> bool:
    """
    DOM automation for Spotify Web: open search URL (or navigate to search),
    wait for results, click first track (or first play button) via DOM.
    No coordinate guessing.
    """
    if not _dom_available_check():
        return False
    song_encoded = quote(song_name)
    url = config.SPOTIFY_WEB_URL + song_encoded
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=headless)
            except Exception:
                browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            _log("dom_controller: navigating to Spotify search")
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2.5)
            clicked = False
            for selector in [SPOTIFY_PLAY_BUTTON, SPOTIFY_FIRST_TRACK_ROW]:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        el.wait_for(state="visible", timeout=6000)
                        el.click()
                        _log(f"dom_controller: clicked Spotify first result (selector: {selector})")
                        clicked = True
                        break
                except Exception as e:
                    _log(f"dom_controller: Spotify selector {selector} failed: {e}")
                    continue
            if not clicked:
                try:
                    clicked = page.evaluate("""() => {
                        const btn = document.querySelector("button[data-testid='play-button']");
                        const row = document.querySelector("div[data-testid='tracklist-row']");
                        if (btn) { btn.click(); return true; }
                        if (row) { row.click(); return true; }
                        return false;
                    }""")
                    if clicked:
                        _log("dom_controller: clicked Spotify first result via JS")
                except Exception:
                    pass
            browser.close()
        return clicked
    except Exception as e:
        _log(f"dom_controller: play_spotify_web failed: {e}")
        return False


def is_dom_available() -> bool:
    """Return True if Playwright is installed and DOM automation can be used."""
    return _dom_available_check()
