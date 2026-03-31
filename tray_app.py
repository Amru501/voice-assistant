"""
Jarvis Assistant - System Tray
Runs in the Windows system tray with a Jarvis icon. No console window.
"""

import os
import sys
import threading

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None
    Image = None
    ImageDraw = None

import config


def _create_default_icon() -> "Image.Image":
    """Create a simple circular icon (Jarvis-style) if no .ico file exists."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer ring (blue/silver)
    draw.ellipse([2, 2, size - 2, size - 2], outline=(100, 149, 237), width=4)
    # Inner circle (dark)
    draw.ellipse([12, 12, size - 12, size - 12], fill=(30, 30, 50), outline=(70, 100, 180))
    # Center dot
    draw.ellipse([26, 26, 38, 38], fill=(100, 149, 237))
    return img


def load_icon():
    """Load tray icon from assets/jarvis_icon.ico or create default."""
    if os.path.isfile(config.ICON_PATH):
        try:
            return Image.open(config.ICON_PATH).convert("RGBA")
        except Exception:
            pass
    return _create_default_icon()


def create_tray_icon(icon_path=None, on_quit=None):
    """
    Create the system tray icon (does not run). Use icon.run() or icon.run_detached().
    Args:
        icon_path: Optional path to .ico (overrides config).
        on_quit: Optional callable() when user chooses Quit from menu.
    Returns:
        pystray.Icon or None if pystray/PIL unavailable.
    """
    if pystray is None or Image is None:
        return None
    path = icon_path or config.ICON_PATH
    if path and os.path.isfile(path):
        try:
            image = Image.open(path).convert("RGBA")
        except Exception:
            image = _create_default_icon()
    else:
        image = _create_default_icon()

    # Resize for tray (typically 16x16 or 32x32)
    image = image.resize((32, 32), Image.Resampling.LANCZOS)

    def on_quit_clicked(icon, item):
        if on_quit:
            on_quit()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Jarvis", lambda *a: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit_clicked, default=True),
    )
    return pystray.Icon("jarvis", image, "Jarvis", menu)


def run_tray(icon_path=None, on_quit=None):
    """
    Run the system tray icon. Blocks until icon is stopped.
    """
    icon = create_tray_icon(icon_path=icon_path, on_quit=on_quit)
    if icon:
        icon.run()


def run_tray_detached(icon_path=None, on_quit=None):
    """
    Run the system tray icon in the background (non-blocking).
    Returns the Icon so caller can call icon.stop() to exit.
    """
    icon = create_tray_icon(icon_path=icon_path, on_quit=on_quit)
    if icon:
        icon.run_detached()
    return icon
