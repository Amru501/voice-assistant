"""
Jarvis Assistant - Configuration
Central place for API keys, paths, and tunable parameters.
"""

import os
import sys

# ---------------------------------------------------------------------------
# API Configuration (set via environment variables or edit here for dev)
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Which AI provider to use: "openai" (ChatGPT) or "gemini"
AI_PROVIDER = os.environ.get("JARVIS_AI_PROVIDER", "openai")

# ---------------------------------------------------------------------------
# Voice / Speech
# ---------------------------------------------------------------------------
# Microphone sample rate (Hz). 16000 is typical for SpeechRecognition.
SAMPLE_RATE = 16000
# Seconds of silence before considering phrase complete (longer = less cut-off, e.g. "play music blinding lights")
PHRASE_TIMEOUT = 4.0
# Energy threshold for considering speech started (adjust if mic is quiet/loud)
ENERGY_THRESHOLD = 300
# Pyttsx3: rate (words per minute), volume 0.0–1.0
TTS_RATE = 150
TTS_VOLUME = 1.0
# Optional: set voice by index if you have multiple (0 = default)
TTS_VOICE_INDEX = 0

# ---------------------------------------------------------------------------
# Hotkey
# ---------------------------------------------------------------------------
# Global hotkey to stop listening and exit safely
EXIT_HOTKEY = "f8"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Base directory (when frozen EXE, use PyInstaller's bundle root so assets/ is found)
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ICON_PATH = os.path.join(BASE_DIR, "assets", "jarvis_icon.ico")

# ---------------------------------------------------------------------------
# Automation
# ---------------------------------------------------------------------------
# Window title substrings to detect music apps (case-insensitive)
SPOTIFY_TITLES = ("spotify",)
# Include domain so we match when window title shows e.g. "music.youtube.com"
YOUTUBE_MUSIC_TITLES = ("youtube music", "music.youtube", "music.youtube.com")
BROWSER_TITLES = ("chrome", "google chrome", "edge", "msedge", "firefox")
# Default browser path if we need to open YouTube Music
CHROME_PATH = os.environ.get("JARVIS_CHROME_PATH", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
# Chrome remote-debugging port for DOM play-button detection in existing tab (attach via CDP)
CHROME_DEBUGGING_PORT = int(os.environ.get("JARVIS_CHROME_DEBUGGING_PORT", "9222"))
YOUTUBE_MUSIC_URL = "https://music.youtube.com"
SPOTIFY_WEB_URL = "https://open.spotify.com/search/"
# DOM automation: False = show browser window (headed), True = run in background
MUSIC_HEADLESS = False
# Chrome profile for DOM (YouTube Music signed in): use a persistent folder so you sign in once.
# Leave empty to use default Jarvis profile under %LOCALAPPDATA%\\Jarvis\\ChromeProfile.
# To use your main Chrome profile (you must close Chrome first), set to your User Data path, e.g.:
# CHROME_USER_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
CHROME_USER_DATA_DIR = os.environ.get("JARVIS_CHROME_USER_DATA", "")
# Browser window size when opening YT Music (large = more like full screen)
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
# If True, use a large fixed viewport instead of --start-maximized (try this if window stays small)
USE_LARGE_VIEWPORT_INSTEAD_OF_MAXIMIZED = False
