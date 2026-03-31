"""
Jarvis Assistant - Status Window
Shows "Jarvis is listening" in a small window that appears in the taskbar.
User can see the app is running and close it via the window X or taskbar.
"""

import os

_overlay_root = None
_on_close_callback = None


def create_listening_overlay(on_close=None):
    """
    Create and show the status window. Call from main thread.
    Uses a normal window (not overrideredirect) so it appears in the taskbar.
    on_close: callable() when user closes the window (X or taskbar).
    """
    global _overlay_root, _on_close_callback
    _on_close_callback = on_close
    try:
        import tkinter as tk
    except ImportError:
        return None

    root = tk.Tk()
    _overlay_root = root

    # Normal window = taskbar button. Title shows in taskbar.
    root.title("Jarvis")
    root.resizable(False, False)
    # Taskbar icon (use project icon if available)
    try:
        import config
        if config.ICON_PATH and os.path.isfile(config.ICON_PATH):
            root.iconbitmap(config.ICON_PATH)
    except Exception:
        pass
    root.attributes("-topmost", False)
    root.attributes("-alpha", 0.95)

    # When user closes window (X or taskbar), exit app
    def on_closing():
        if _on_close_callback:
            _on_close_callback()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Styling: dark bar, light text
    bg_color = "#0d1b2a"
    text_color = "#e8e8e8"
    highlight_color = "#00d4aa"

    root.configure(bg=bg_color)

    frame = tk.Frame(root, bg=bg_color, padx=24, pady=14)
    frame.pack()

    label = tk.Label(
        frame,
        text="Jarvis is listening",
        fg=text_color,
        bg=bg_color,
        font=("Segoe UI", 14, "bold"),
    )
    label.pack()

    accent = tk.Frame(frame, height=3, bg=highlight_color, width=140)
    accent.pack(pady=(8, 0))

    hint = tk.Label(
        frame,
        text="Press F8 or close this window to exit",
        fg="#8899aa",
        bg=bg_color,
        font=("Segoe UI", 9, "normal"),
    )
    hint.pack(pady=(10, 0))

    root.update_idletasks()
    w = max(280, root.winfo_reqwidth())
    h = max(100, root.winfo_reqheight())
    root.minsize(w, h)

    # Center at top of primary screen
    try:
        sw = root.winfo_screenwidth()
        x = max(0, sw // 2 - w // 2)
        root.geometry(f"{w}x{h}+{x}+24")
    except Exception:
        root.geometry(f"{w}x{h}+400+24")

    root.lift()
    root.deiconify()
    root.update()
    return root


def update_overlay():
    """Process one tk event (call from main loop so window stays responsive)."""
    global _overlay_root
    if _overlay_root is None:
        return
    try:
        _overlay_root.update_idletasks()
        _overlay_root.update()
    except Exception:
        pass


def hide_listening_overlay():
    """Close the status window. Call from main thread."""
    global _overlay_root
    root = _overlay_root
    _overlay_root = None
    if root is None:
        return
    try:
        root.destroy()
    except Exception:
        pass


def show_listening_overlay(on_close=None):
    """
    Create and show the status window (main thread only).
    on_close: callable() when user closes the window; use to trigger app exit.
    """
    global _overlay_root
    if _overlay_root is not None:
        return
    create_listening_overlay(on_close=on_close)
