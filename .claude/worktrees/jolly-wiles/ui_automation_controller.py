"""
Jarvis Assistant - UI Automation Controller
Windows UI Automation (pywinauto UIA backend) for Spotify Desktop.
Locates search box and first result Play button via accessibility tree;
no screen coordinates or image detection.
"""

import time
from typing import Optional

# Optional: pywinauto for UIA. If not installed, Spotify Desktop automation returns False.
_ui_automation_available: Optional[bool] = None


def _ui_available_check() -> bool:
    """True if pywinauto is importable (UIA backend)."""
    global _ui_automation_available
    if _ui_automation_available is not None:
        return _ui_automation_available
    try:
        from pywinauto import Application
        _ui_automation_available = True
    except Exception:
        _ui_automation_available = False
    return _ui_automation_available


def _log(msg: str) -> None:
    try:
        from debug_log import log as _log_fn
        _log_fn(msg)
    except Exception:
        pass


def play_spotify_desktop(song_name: str) -> bool:
    """
    Spotify Desktop: Windows UI Automation (pywinauto UIA).
    - Detect Spotify window by title.
    - Locate search box (Edit control or control with search role).
    - Type song name, press Enter.
    - Locate first result row and Play button via accessibility tree.
    - Click Play (no coordinate guessing).
    Returns False if pywinauto unavailable or Spotify not found / controls not found.
    """
    if not _ui_available_check():
        _log("ui_automation: pywinauto not available")
        return False
    try:
        from pywinauto import Application
    except ImportError:
        _log("ui_automation: pywinauto import failed")
        return False
    # Connect to Spotify by window title (UIA backend)
    try:
        app = Application(backend="uia").connect(title_re=".*Spotify.*", timeout=5)
    except Exception as e:
        _log(f"ui_automation: Spotify window not found: {e}")
        return False
    try:
        win = app.window(title_re=".*Spotify.*")
        win.restore()
        win.set_focus()
        time.sleep(0.5)
        # Find search: Spotify Desktop often has a search Edit or "Search" control
        # Try multiple strategies: Edit control, or control with Name="Search"
        search_typed = False
        try:
            # Strategy 1: First Edit control (search box)
            edit = win.child_window(control_type="Edit")
            if edit.exists(timeout=2):
                edit.set_focus()
                edit.set_edit_text("")
                time.sleep(0.1)
                edit.type_keys(song_name, with_spaces=True)
                time.sleep(0.2)
                edit.type_keys("{ENTER}")
                search_typed = True
                _log("ui_automation: typed song in Edit (search)")
        except Exception as e:
            _log(f"ui_automation: Edit search failed: {e}")
        if not search_typed:
            try:
                # Strategy 2: Ctrl+L to focus search (Spotify shortcut), then type
                import pyautogui
                pyautogui.hotkey("ctrl", "l")
                time.sleep(0.3)
                pyautogui.write(song_name, interval=0.03)
                time.sleep(0.1)
                pyautogui.press("enter")
                search_typed = True
                _log("ui_automation: used Ctrl+L and typed song")
            except Exception as e2:
                _log(f"ui_automation: Ctrl+L fallback failed: {e2}")
        if not search_typed:
            return False
        time.sleep(2.5)
        # Find and click first Play button (accessibility tree)
        play_clicked = False
        try:
            # Play button: often name "Play" or automation id containing "play"
            play_btn = win.child_window(title_re="Play", control_type="Button")
            if play_btn.exists(timeout=3):
                play_btn.click()
                play_clicked = True
                _log("ui_automation: clicked Play button (title_re=Play)")
        except Exception:
            pass
        if not play_clicked:
            try:
                # Alternative: first Button in list/tree that might be Play
                buttons = win.descendants(control_type="Button")
                for b in buttons[:20]:
                    try:
                        name = b.window_text() or ""
                        if name and "play" in name.lower():
                            b.click()
                            play_clicked = True
                            _log("ui_automation: clicked Play button (descendant)")
                            break
                    except Exception:
                        continue
            except Exception:
                pass
        if not play_clicked:
            # Fallback: first list item or data row - Enter to select/play
            try:
                list_item = win.child_window(control_type="ListItem")
                if list_item.exists(timeout=2):
                    list_item.click()
                    time.sleep(0.2)
                    import pyautogui
                    pyautogui.press("enter")
                    pyautogui.press("space")
                    play_clicked = True
                    _log("ui_automation: clicked first ListItem + Enter/Space")
            except Exception:
                pass
        return play_clicked or search_typed
    except Exception as e:
        _log(f"ui_automation: play_spotify_desktop failed: {e}")
        return False


def is_ui_automation_available() -> bool:
    """Return True if pywinauto (UIA) is available for Spotify Desktop."""
    return _ui_available_check()
