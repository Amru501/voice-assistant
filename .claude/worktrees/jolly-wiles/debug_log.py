"""
Jarvis Assistant - Debug log
Writes to jarvis_debug.txt so we can see what was heard and any errors.
Uses TEMP folder so the file is always writable (e.g. when EXE is in Program Files or OneDrive).
"""

import os
import sys
import traceback
from datetime import datetime

_log_path = None


def _get_log_path():
    global _log_path
    if _log_path is not None:
        return _log_path
    # Use TEMP so we can always write (EXE folder may be read-only)
    base = os.environ.get("TEMP", os.environ.get("TMP", os.path.expanduser("~")))
    _log_path = os.path.join(base, "jarvis_debug.txt")
    return _log_path


def log(msg: str) -> None:
    """Append a line to the debug log. Never raises."""
    try:
        path = _get_log_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def get_log_path() -> str:
    """Return the path to the log file (so user can find it)."""
    return _get_log_path()


def log_exception() -> None:
    """Append the current exception traceback to the debug log."""
    try:
        log(traceback.format_exc())
    except Exception:
        pass
