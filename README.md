# Jarvis Voice Assistant

A Windows desktop AI assistant that runs silently in the system tray, listens for voice commands, and controls your desktop — music, apps, volume, media — with a calm, Jarvis-like personality.

---

## Features

- Runs in the **system tray** with no console window
- **Voice in / voice out** — microphone input + text-to-speech (pyttsx3)
- **AI-powered intent parsing** via Gemini or OpenAI (ChatGPT)
- **Smart music control** — tries DOM (YouTube / YT Music / Spotify Web) first, then UI Automation (Spotify Desktop), then keyboard fallback
- **Desktop automation** — open/close apps, volume up/down, pause/play media
- **F8 hotkey** to stop listening and exit safely

---

## Requirements

### System

| Requirement | Details |
|---|---|
| OS | Windows 10 / 11 |
| Python | 3.10, 3.11, or 3.12 (3.12 recommended) |
| Microphone | Any working input device |
| API Key | OpenAI **or** Google Gemini (at least one) |

### Python Packages

Install all dependencies at once:

```powershell
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| `SpeechRecognition` | Microphone speech-to-text |
| `PyAudio` | Audio input from microphone |
| `pyttsx3` | Text-to-speech (offline, no API needed) |
| `openai` | ChatGPT intent parsing (optional) |
| `google-generativeai` | Gemini intent parsing (optional) |
| `playwright` | DOM automation for YouTube / Spotify Web |
| `pywinauto` | UI Automation for Spotify Desktop |
| `pyautogui` | Keyboard/mouse fallback automation |
| `pygetwindow` | Window detection and focus |
| `keyboard` | Global hotkey (F8 to exit) |
| `pystray` | System tray icon |
| `Pillow` | Icon rendering for tray |
| `pywin32` | Windows API (required for EXE build) |

> **PyAudio on Windows**: If `pip install PyAudio` fails, install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) first, or download a prebuilt wheel from [Gohlke's wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install with `pip install PyAudio-0.2.13-cp312-cp312-win_amd64.whl`.

> **Playwright browser**: After installing, run once:
> ```powershell
> playwright install chromium
> ```

---

## Setup

### 1. Clone the repo

```powershell
git clone https://github.com/Amru501/voice-assistant.git
cd "voice-assistant"
```

### 2. Create a virtual environment (recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
playwright install chromium
```

### 4. Set your API key

Choose one AI provider:

**OpenAI (ChatGPT)**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:JARVIS_AI_PROVIDER = "openai"
```

**Google Gemini**
```powershell
$env:GEMINI_API_KEY = "your-key-here"
$env:JARVIS_AI_PROVIDER = "gemini"
```

You can also edit `config.py` directly for local development — just don't commit your real keys.

### 5. Run

```powershell
# With console (for debugging)
python main.py

# Without console window
pythonw main.py
```

Jarvis appears in the system tray. Speak a command like:
- *"Play Blinding Lights"*
- *"Volume up"*
- *"Open Notepad"*
- *"Pause music"*

Press **F8** to exit.

---

## Project Structure

```
voice-assistant/
├── main.py                      # Entry point — tray + voice loop + F8 exit
├── voice_engine.py              # Speech-to-text + TTS
├── jarvis_brain.py              # AI intent understanding (Gemini / OpenAI)
├── intent_parser.py             # Parse AI response to JSON intent
├── automation_engine.py         # Orchestrates DOM / UI Automation / keyboard
├── dom_controller.py            # Playwright DOM automation (YouTube, Spotify Web)
├── ui_automation_controller.py  # pywinauto UIA (Spotify Desktop)
├── tray_app.py                  # System tray icon and menu
├── config.py                    # API keys, paths, settings
├── requirements.txt
├── build_exe.ps1                # Helper script to build EXE
├── kill_jarvis.ps1              # Force-kill script (use before rebuilding)
├── assets/
│   └── jarvis_icon.ico
└── README.md
```

---

## Building an EXE

```powershell
# Option A — use the build script (recommended)
.\build_exe.ps1

# Option B — manual
pip install pyinstaller
pyinstaller --onefile --noconsole --name "Jarvis" --icon assets\jarvis_icon.ico main.py
```

Output: `dist\Jarvis.exe` — double-click to run.

> If you get "Access is denied" when rebuilding, Jarvis is still running. Run `.\kill_jarvis.ps1` or end it via Task Manager, then rebuild.

> Antivirus may flag PyInstaller EXEs. Add a folder exclusion if needed.

---

## Debugging

If commands are heard but nothing happens, check the debug log:

```
%TEMP%\jarvis_debug.txt
```

It logs:
- `Heard: "..."` — speech was recognized
- `Speech: could not understand` — Google STT returned nothing
- `Intent: ...` — parsed command
- `Done: ...` — automation result
- Full exception tracebacks

---

## Configuration

Edit `config.py` to tune:

| Key | Description |
|---|---|
| `AI_PROVIDER` | `"openai"` or `"gemini"` |
| `TTS_RATE` / `TTS_VOLUME` | Voice speed and volume |
| `EXIT_HOTKEY` | Default: `"f8"` |
| `MUSIC_HEADLESS` | `False` = show browser, `True` = run headless |
| `CHROME_PATH` | Path to Chrome if not auto-detected |

---

## License

Use and modify freely. Keep API keys out of version control.
