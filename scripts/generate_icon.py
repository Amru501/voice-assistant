"""
Generate assets/jarvis_icon.ico for tray and EXE build.
Run: python scripts/generate_icon.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Install Pillow: pip install Pillow")
    sys.exit(1)


def create_icon(size: int = 64) -> Image.Image:
    """Create a Jarvis-style circular icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer ring (blue/silver)
    draw.ellipse([2, 2, size - 2, size - 2], outline=(100, 149, 237), width=max(2, size // 16))
    # Inner circle (dark)
    margin = size // 5
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(30, 30, 50), outline=(70, 100, 180))
    # Center dot
    center_margin = size // 2 - size // 8
    draw.ellipse([center_margin, center_margin, size - center_margin, size - center_margin], fill=(100, 149, 237))
    return img


def create_play_button_png(size: int = 40) -> Image.Image:
    """Create a play (triangle) icon for on-screen matching (e.g. YouTube Music)."""
    img = Image.new("RGBA", (size, size), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)
    # Right-pointing triangle (play icon), centered
    margin = size // 5
    left = margin
    right = size - margin
    top = margin
    bottom = size - margin
    # Triangle: left edge (vertical), tip on right
    draw.polygon([
        (left, top),
        (left, bottom),
        (right, size // 2),
    ], fill=(255, 255, 255))
    return img


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(base, "assets")
    os.makedirs(assets, exist_ok=True)
    path = os.path.join(assets, "jarvis_icon.ico")
    img = create_icon(64)
    img.save(path, format="ICO", sizes=[(16, 16), (32, 32), (64, 64)])
    print("Saved:", path)
    # Play button for automation (find Play on screen)
    play_path = os.path.join(assets, "play_button.png")
    create_play_button_png(40).save(play_path)
    print("Saved:", play_path)


if __name__ == "__main__":
    main()
