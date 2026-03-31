"""
Jarvis Assistant - Main Entry Point
Runs silently in the background (no console), system tray, continuous voice listening.
Global hotkey F8 stops listening and exits safely.
"""

import sys
import threading
import time

# Prevent console window on Windows when double-clicking (use pythonw.exe or build with --noconsole)
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Attach to parent process console if any; otherwise no console
        kernel32.FreeConsole()
    except Exception:
        pass

import config
from voice_engine import VoiceEngine
from jarvis_brain import understand
from automation_engine import execute_intent
from tray_app import run_tray_detached
from listening_overlay import show_listening_overlay, hide_listening_overlay, update_overlay
from debug_log import log, log_exception, get_log_path

# Windows: native status window (always shows in taskbar; tkinter can fail in EXE)
if sys.platform == "win32":
    try:
        from status_window_win32 import (
            create_win32_status_window,
            pump_win32_status,
            hide_win32_status,
        )
    except ImportError:
        create_win32_status_window = None
        pump_win32_status = lambda: None
        hide_win32_status = lambda: None
else:
    create_win32_status_window = None
    pump_win32_status = lambda: None
    hide_win32_status = lambda: None

# Global shutdown event: set by F8 or tray Quit
_shutdown = threading.Event()
_tray_icon = None


def _on_phrase(text: str) -> None:
    """
    Called when user speech is recognized. Run in a worker thread so the voice
    listener stays responsive and the main thread is not blocked by API/TTS.
    """
    if _shutdown.is_set():
        return
    log(f"Heard: {text!r}")
    def _run():
        if _shutdown.is_set():
            return
        try:
            intent = understand(text)
            if not intent:
                log("No intent returned")
                return
            log(f"Intent: {intent}")
            if _shutdown.is_set():
                return
            log("Executing intent...")
            success, message = execute_intent(intent)
            if _shutdown.is_set():
                return
            log(f"Done: {message}")
            if voice_engine:
                voice_engine.speak(message, block=True)
        except Exception:
            log_exception()
    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _exit_safely() -> None:
    """Stop listening, stop tray, hide status window, exit process."""
    global _tray_icon
    _shutdown.set()
    hide_listening_overlay()
    hide_win32_status()
    if voice_engine:
        voice_engine.shutdown()
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
        _tray_icon = None
    try:
        keyboard.unhook_all()
    except Exception:
        pass
    sys.exit(0)


# Lazy import keyboard so we can exit if missing
keyboard = None
voice_engine = None


def main() -> None:
    global keyboard, voice_engine, _tray_icon
    voice_engine_ref = None

    # Create debug log immediately so user can find it (TEMP\jarvis_debug.txt)
    log("Jarvis started")
    log(f"Log file: {get_log_path()}")

    # Optional: hide console (already tried FreeConsole above; PyInstaller uses --noconsole)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0
            )
        except Exception:
            pass

    try:
        import keyboard as kb
        keyboard = kb
    except ImportError:
        keyboard = None

    # System tray (detached so main thread can run voice loop)
    def on_quit():
        _shutdown.set()

    _tray_icon = run_tray_detached(on_quit=on_quit)
    if not _tray_icon:
        # Fallback: run without tray (e.g. missing pystray)
        pass

    # Global hotkey F8 to exit
    if keyboard:
        try:
            keyboard.add_hotkey(config.EXIT_HOTKEY, _exit_safely, suppress=False)
        except Exception:
            pass

    # Status window FIRST so user always sees the app is running
    # On Windows: native Win32 window (always shows in taskbar, works in EXE)
    # Else: tkinter overlay
    if sys.platform == "win32" and create_win32_status_window:
        create_win32_status_window(on_close_callback=_exit_safely)
    else:
        show_listening_overlay(on_close=_exit_safely)

    # Voice engine: listen continuously, on phrase -> brain -> automation -> speak
    voice_engine_ref = VoiceEngine(on_phrase_callback=_on_phrase)
    voice_engine = voice_engine_ref
    voice_engine_ref.start_listening()
    log("Listening started")

    # Main loop: pump window messages often so window stays responsive (avoids "Not Responding")
    try:
        while not _shutdown.is_set():
            if sys.platform == "win32" and create_win32_status_window:
                pump_win32_status()
            else:
                update_overlay()
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    _exit_safely()


if __name__ == "__main__":
    main()
