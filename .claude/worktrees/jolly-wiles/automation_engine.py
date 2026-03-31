"""
Jarvis Assistant - Automation Engine
Platform detection (pygetwindow) + control logic.
Music: DOM first (YouTube/YT Music/Spotify Web), then UI Automation (Spotify Desktop),
then keyboard fallback. No screen coordinates or fragile clicking.
"""

import os
import time
import subprocess
import threading
from urllib.parse import quote
from typing import Any, Dict, List, Optional, Tuple

try:
    import pygetwindow as gw
except Exception:
    gw = None

import pyautogui

import config

# Fail-safe: move mouse to corner to abort pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

# ---------------------------------------------------------------------------
# Music: DOM first, UI Automation (Spotify Desktop), keyboard fallback
# ---------------------------------------------------------------------------
YOUTUBE_FIRST_RESULT_TABS = 8
SPOTIFY_FIRST_RESULT_TABS = 5
YOUTUBE_RESULTS_WAIT_SEC = 4.0
SPOTIFY_RESULTS_WAIT_SEC = 2.5


def get_all_windows() -> List[Any]:
    """Return list of window objects (title, etc.) from pygetwindow."""
    if gw is None:
        return []
    try:
        return list(gw.getAllWindows())
    except Exception:
        return []


def get_window_titles() -> List[str]:
    """Return list of non-empty window titles."""
    titles = []
    for w in get_all_windows():
        try:
            t = (getattr(w, "title", None) or "").strip()
            if t:
                titles.append(t)
        except Exception:
            continue
    return titles


def _is_browser_title(title_lower: str) -> bool:
    """True if window looks like a browser (Chrome, Edge, Firefox)."""
    for key in config.BROWSER_TITLES:
        if key in title_lower:
            return True
    return False


def find_best_music_window() -> Optional[Tuple[Any, str]]:
    """
    Platform detection: find the best window to play music (pygetwindow).
    Priority: 1) Spotify desktop, 2) YT Music desktop, 3) Browser+Spotify tab,
    4) Browser+YouTube/YT Music tab, 5) Any browser (reuse tab).
    Returns (window, context) or None. Context: spotify_app, ytmusic_app,
    browser_spotify, browser_ytmusic, browser_any.
    """
    candidates = []  # (priority, window, context). Lower priority = better.
    any_browser = None  # fallback: first Chrome/Edge window
    for w in get_all_windows():
        try:
            t = (getattr(w, "title", None) or "").strip()
            if not t:
                continue
            tl = t.lower()
            is_browser = _is_browser_title(tl)
            if is_browser and any_browser is None:
                any_browser = w
            # Spotify
            for key in config.SPOTIFY_TITLES:
                if key in tl:
                    if is_browser:
                        candidates.append((3, w, "browser_spotify"))
                    else:
                        candidates.append((1, w, "spotify_app"))
                    break
            else:
                # YouTube Music (include "youtube" alone so we catch YT Music tab when title is short)
                for key in config.YOUTUBE_MUSIC_TITLES:
                    if key in tl:
                        if is_browser:
                            candidates.append((4, w, "browser_ytmusic"))
                        else:
                            candidates.append((2, w, "ytmusic_app"))
                        break
                else:
                    if "youtube" in tl and is_browser:
                        candidates.append((4, w, "browser_ytmusic"))
        except Exception:
            continue
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return (candidates[0][1], candidates[0][2])
    if any_browser is not None:
        return (any_browser, "browser_any")
    return None


def focus_window(win: Any) -> bool:
    """Focus and restore a window. Return True if successful."""
    if win is None:
        return False
    try:
        if hasattr(win, "restore"):
            win.restore()
        if hasattr(win, "activate"):
            win.activate()
        time.sleep(0.3)
        return True
    except Exception:
        return False


def _focus_search_bar_and_type(query: str, press_enter: bool = True) -> None:
    """Keyboard-only: focus search/address bar (Ctrl+L), type query, optionally Enter."""
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.2)
    pyautogui.write(query, interval=0.03)
    if press_enter:
        time.sleep(0.1)
        pyautogui.press("enter")


def _navigate_to_url(url: str) -> None:
    """Keyboard-only: focus address bar (Ctrl+L), type URL, Enter (browser)."""
    pyautogui.hotkey("ctrl", "l")
    time.sleep(0.2)
    pyautogui.write(url, interval=0.02)
    time.sleep(0.1)
    pyautogui.press("enter")


def _play_via_youtube_keyboard(win: Any, song_name: str, already_at_search_url: bool = False) -> None:
    """
    YouTube / YouTube Music: focus window, go to search URL in current tab, then detect play button
    via DOM (CDP) if Chrome has remote-debugging port; else Tab to first result, Enter, Space.
    When navigating, switch to first tab (Ctrl+1) first so we use the YT Music tab, not a blank one.
    """
    focus_window(win)
    time.sleep(0.5)
    song_plus = song_name.replace(" ", "+")
    search_url = "https://music.youtube.com/search?q=" + song_plus
    if not already_at_search_url:
        _log("play_song: switch to first tab then navigate to YouTube Music search")
        pyautogui.hotkey("ctrl", "1")  # first tab is usually YT Music; avoid navigating a blank tab
        time.sleep(0.3)
        _navigate_to_url(search_url)
    time.sleep(YOUTUBE_RESULTS_WAIT_SEC)
    # Prefer DOM play-button detection (attach via CDP); fallback to Tab/Enter/Space
    try:
        from dom_controller import try_click_yt_music_via_cdp
        if try_click_yt_music_via_cdp(wait_sec=1.0):
            _log("play_song: played via DOM (CDP)")
            return
    except Exception as e:
        _log(f"play_song: CDP DOM failed, using Tab: {e}")
    _log("play_song: Tab to first result, Enter, Space")
    pyautogui.press("tab", presses=YOUTUBE_FIRST_RESULT_TABS, interval=0.25)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.2)
    pyautogui.press("space")


def _play_via_spotify_keyboard(win: Any, song_name: str) -> None:
    """
    Spotify desktop app playback (keyboard-only).
    - Focus window, Ctrl+L to jump to search, type song, Enter.
    - Wait for results, Tab to first result, Enter, Space to ensure playback.
    """
    focus_window(win)
    time.sleep(0.5)
    _log("play_song: Spotify search (Ctrl+L), type, Enter")
    _focus_search_bar_and_type(song_name, press_enter=True)
    time.sleep(SPOTIFY_RESULTS_WAIT_SEC)
    _log("play_song: Tab to first result, Enter, Space")
    pyautogui.press("tab", presses=SPOTIFY_FIRST_RESULT_TABS, interval=0.25)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.2)
    pyautogui.press("space")


def _play_via_spotify_browser_keyboard(win: Any, song_name: str) -> None:
    """
    Spotify in browser: switch to first tab, navigate to search URL, then DOM (CDP) or Tab/Enter/Space.
    """
    focus_window(win)
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "1")  # first tab is usually Spotify; avoid navigating a blank tab
    time.sleep(0.3)
    song_encoded = quote(song_name)
    _log("play_song: navigating to Spotify search in browser")
    _navigate_to_url(config.SPOTIFY_WEB_URL + song_encoded)
    time.sleep(SPOTIFY_RESULTS_WAIT_SEC)
    try:
        from dom_controller import try_click_spotify_via_cdp
        if try_click_spotify_via_cdp(wait_sec=1.0):
            _log("play_song: played via DOM (CDP)")
            return
    except Exception as e:
        _log(f"play_song: CDP DOM failed, using Tab: {e}")
    _log("play_song: Tab to first result, Enter, Space")
    pyautogui.press("tab", presses=SPOTIFY_FIRST_RESULT_TABS, interval=0.25)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.2)
    pyautogui.press("space")


def _log(msg: str) -> None:
    try:
        from debug_log import log as _log_fn
        _log_fn(msg)
    except Exception:
        pass


def play_song(song_name: str, platform_hint: Optional[str] = None) -> Tuple[bool, str]:
    """
    Music playback: DOM first (YouTube/YT Music/Spotify Web), then UI Automation
    (Spotify Desktop), then keyboard fallback.
    Strategy: Spotify Web -> DOM; YouTube/YT Music -> DOM; Spotify Desktop -> UIA;
    else open YouTube Music -> DOM; fallback -> keyboard.
    Returns (success, message) for TTS.
    """
    _log(f"play_song: starting for {song_name!r}")
    song_plus = song_name.replace(" ", "+")
    song_encoded = quote(song_name)

    # --- Try same-tab CDP first: if DOM browser (or any Chrome with debugging) is already open, use that tab only ---
    # This ensures the second request always runs in the same tab as the first (DOM browser), not in user's Chrome.
    try:
        from dom_controller import navigate_yt_music_tab_and_play_via_cdp
        if navigate_yt_music_tab_and_play_via_cdp(song_name):
            _log("play_song: done (same-tab CDP YT Music)")
            return True, "Playing on YouTube."
    except Exception as e:
        _log(f"play_song: same-tab CDP YT Music failed: {e}")
    try:
        from dom_controller import navigate_spotify_tab_and_play_via_cdp
        if navigate_spotify_tab_and_play_via_cdp(song_name):
            _log("play_song: done (same-tab CDP Spotify)")
            return True, "Playing on Spotify."
    except Exception as e:
        _log(f"play_song: same-tab CDP Spotify failed: {e}")

    # Platform detection (getAllWindows can hang from background thread; use timeout)
    best = None
    def _find():
        nonlocal best
        best = find_best_music_window()
    t = threading.Thread(target=_find, daemon=True)
    t.start()
    t.join(timeout=8.0)  # allow time for getAllWindows on Windows so we find existing music tab
    if t.is_alive():
        _log("play_song: find_best_music_window timed out")

    # --- Spotify Web (browser): keyboard in found window ---
    if best:
        win, context = best
        try:
            title = getattr(win, "title", None) or ""
            _log(f"play_song: platform {context!r} window {title!r}")
        except Exception:
            _log(f"play_song: platform {context!r}")

        # --- Spotify Web: search and play inside the existing Spotify tab only (CDP first) ---
        if context == "browser_spotify":
            try:
                from dom_controller import navigate_spotify_tab_and_play_via_cdp
                if navigate_spotify_tab_and_play_via_cdp(song_name):
                    return True, "Playing on Spotify."
            except Exception as e:
                _log(f"play_song: Spotify same-tab CDP failed: {e}")
            _play_via_spotify_browser_keyboard(win, song_name)
            return True, "Playing on Spotify."

        # --- YouTube / YT Music / any browser: search and play inside the existing YT Music tab only (CDP first) ---
        if context in ("browser_ytmusic", "browser_any"):
            try:
                from dom_controller import navigate_yt_music_tab_and_play_via_cdp
                if navigate_yt_music_tab_and_play_via_cdp(song_name):
                    return True, "Playing on YouTube."
            except Exception as e:
                _log(f"play_song: YT Music same-tab CDP failed: {e}")
            _play_via_youtube_keyboard(win, song_name, already_at_search_url=False)
            return True, "Playing on YouTube."

        # --- Spotify Desktop: UI Automation first, then keyboard fallback ---
        if context == "spotify_app":
            try:
                from ui_automation_controller import play_spotify_desktop
                if play_spotify_desktop(song_name):
                    _log("play_song: done (Spotify Desktop UIA)")
                    return True, "Playing on Spotify."
            except Exception as e:
                _log(f"play_song: Spotify Desktop UIA failed: {e}")
            _play_via_spotify_keyboard(win, song_name)
            return True, "Playing on Spotify."

        # --- YT Music desktop app: keyboard only (no DOM for desktop app) ---
        if context == "ytmusic_app":
            _play_via_youtube_keyboard(win, song_name, already_at_search_url=False)
            return True, "Playing on YouTube."

    # --- No music window: retry find (may have timed out), then reuse any browser in same tab ---
    _log("play_song: no music window, retry find then reuse any browser")
    fallback_best = None
    def _find_any():
        nonlocal fallback_best
        try:
            fallback_best = find_best_music_window()
        except Exception:
            pass
    t_fb = threading.Thread(target=_find_any, daemon=True)
    t_fb.start()
    t_fb.join(timeout=8.0)  # longer timeout so we find existing Chrome/YT Music
    if fallback_best is not None:
        win, ctx = fallback_best
        _log(f"play_song: found window on retry ({ctx}), using current tab")
        _play_via_youtube_keyboard(win, song_name, already_at_search_url=False)
        return True, "Playing on YouTube."

    # --- No browser at all: open DOM browser (Playwright) and play there; later requests reuse same tab via CDP ---
    _log("play_song: no browser found - open DOM browser (Playwright) and play")
    try:
        from dom_controller import play_youtube_music
        headless = getattr(config, "MUSIC_HEADLESS", False)
        if play_youtube_music(song_name, headless=headless):
            _log("play_song: done (DOM browser)")
            return True, "Song started."
    except Exception as e:
        _log(f"play_song: DOM browser failed: {e}")
    # Fallback if Playwright not available or failed
    _log("play_song: fallback - open Chrome and use keyboard")
    try:
        subprocess.Popen(
            [config.CHROME_PATH, "https://music.youtube.com/search?q=" + song_plus],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3.0)
        chrome_win = None
        def _get_chrome():
            nonlocal chrome_win
            try:
                found = find_best_music_window()
                if found:
                    chrome_win, _ = found
            except Exception:
                pass
        t2 = threading.Thread(target=_get_chrome, daemon=True)
        t2.start()
        t2.join(timeout=2.0)
        _play_via_youtube_keyboard(chrome_win, song_name, already_at_search_url=True)
        return True, "Song started."
    except Exception as e:
        _log(f"play_song: Chrome failed {e}")
        try:
            import webbrowser
            webbrowser.open("https://music.youtube.com/search?q=" + song_plus)
            time.sleep(YOUTUBE_RESULTS_WAIT_SEC)
            _play_via_youtube_keyboard(None, song_name, already_at_search_url=True)
            return True, "Song started."
        except Exception as e2:
            _log(f"play_song: webbrowser failed {e2}")
            return False, "Could not start playback."


def open_app(app_name: str) -> bool:
    """Open an application by name (e.g. notepad, chrome). Uses shell start."""
    name = app_name.lower().strip()
    commands = {
        "notepad": "notepad",
        "chrome": config.CHROME_PATH,
        "spotify": "spotify",
        "calculator": "calc",
        "cmd": "cmd",
        "explorer": "explorer",
    }
    exe = commands.get(name) or app_name
    try:
        subprocess.Popen(
            exe,
            shell=(exe == app_name),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def close_app(app_name: str) -> bool:
    """Try to close a window by title containing app_name."""
    app_lower = app_name.lower()
    for w in get_all_windows():
        try:
            t = (getattr(w, "title", None) or "").lower()
            if app_lower in t and hasattr(w, "close"):
                w.close()
                return True
        except Exception:
            continue
    return False


def volume_up() -> None:
    """Simulate volume up key."""
    pyautogui.press("volumeup", presses=3, interval=0.05)


def volume_down() -> None:
    """Simulate volume down key."""
    pyautogui.press("volumedown", presses=3, interval=0.05)


def set_volume_level(level: int) -> None:
    """Approximate: level 0-100. Use volume keys to approach (crude)."""
    level = max(0, min(100, level))
    # No direct API here; use multiple volume key presses as rough approximation
    pyautogui.press("volumedown", presses=50, interval=0.02)
    time.sleep(0.2)
    presses = int((level / 100.0) * 50)
    pyautogui.press("volumeup", presses=presses, interval=0.02)


def pause_media() -> None:
    """Simulate media pause (e.g. space or media key)."""
    pyautogui.press("playpause")


def play_media() -> None:
    """Simulate media play."""
    pyautogui.press("playpause")


def execute_intent(intent: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Execute a structured intent from Jarvis brain.
    Returns (success, short_message) for TTS.
    """
    cmd = (intent.get("intent") or "").strip().lower()
    if not cmd or cmd == "unknown":
        return False, "I didn't understand that."
    if cmd == "play_song":
        song = (intent.get("song") or intent.get("query") or "").strip()
        if not song:
            return False, "Which song?"
        # "play music" or "play music album" with no real song name = likely cut off or misheard
        if song.lower() in ("music", "album"):
            return False, "Say the song name. For example: play music Blinding Lights."
        success, message = play_song(song, intent.get("platform"))
        return success, message
    if cmd == "open_app":
        app = intent.get("app") or ""
        if not app:
            return False, "Which app?"
        if open_app(app):
            if app.lower().strip() == "spotify":
                return True, "Launching Spotify."
            return True, "Done."
        return False, "Could not open that app."
    if cmd == "close_app":
        app = intent.get("app") or ""
        if not app:
            return False, "Which app?"
        if close_app(app):
            return True, "Task completed."
        return False, "Could not close that app."
    if cmd == "volume_up":
        volume_up()
        return True, "Done."
    if cmd == "volume_down":
        volume_down()
        return True, "Done."
    if cmd == "set_volume":
        vol = intent.get("volume")
        if vol is not None:
            set_volume_level(vol)
            return True, "Done."
        return False, "Specify a volume level."
    if cmd == "pause_media":
        pause_media()
        return True, "Done."
    if cmd == "play_media":
        play_media()
        return True, "Done."
    return False, "Standing by."
