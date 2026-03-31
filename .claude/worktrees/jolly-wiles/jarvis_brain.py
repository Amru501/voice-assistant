"""
Jarvis Assistant - Jarvis Brain
Uses Gemini or ChatGPT API to understand user intent and return structured JSON.
Reasons before acting and chooses the best approach.
"""

import json
from typing import Any, Dict, Optional

import config

# Optional imports for AI providers
_openai_client = None
_gemini_model = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    return _gemini_model


SYSTEM_PROMPT = """You are Jarvis, a calm, intelligent AI assistant. You understand voice commands and respond with a single JSON object only—no other text.

Rules:
- Respond ONLY with valid JSON. No markdown, no explanation.
- Use these intents when appropriate: play_song, open_app, close_app, volume_up, volume_down, set_volume, pause_media, play_media, search, unknown.
- For "play [song name]" or "play music [song name]" use intent "play_song" and "song" = the song name only (e.g. "Blinding Lights"). Optionally "platform" (e.g. "youtube_music", "spotify").
- For "open [app]" use intent "open_app" and "app" (e.g. "notepad", "chrome").
- For "close [app]" use intent "close_app" and "app".
- For volume: volume_up, volume_down, or set_volume with "volume" (0-100).
- For pause/play media use pause_media or play_media.
- Be minimal and decisive. Choose the best interpretation of the user's intent.
- If unclear, use intent "unknown" and optional "query" with the raw request.
"""


def understand(user_text: str) -> Optional[Dict[str, Any]]:
    """
    Send user speech to AI, get back structured intent JSON.
    Returns dict with keys like intent, song, platform, app, etc., or None on error.
    """
    if not user_text or not user_text.strip():
        return None
    user_text = user_text.strip()
    provider = (config.AI_PROVIDER or "openai").lower()
    if provider == "gemini":
        return _ask_gemini(user_text)
    return _ask_openai(user_text)


def _ask_openai(user_text: str) -> Optional[Dict[str, Any]]:
    try:
        client = _get_openai_client()
        if not config.OPENAI_API_KEY:
            return _fallback_intent(user_text)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=256,
        )
        content = (resp.choices[0].message.content or "").strip()
        return _parse_and_normalize(content, user_text)
    except Exception:
        return _fallback_intent(user_text)


def _ask_gemini(user_text: str) -> Optional[Dict[str, Any]]:
    try:
        model = _get_gemini_model()
        if not config.GEMINI_API_KEY:
            return _fallback_intent(user_text)
        resp = model.generate_content(
            SYSTEM_PROMPT + "\n\nUser said: " + user_text,
            generation_config={"temperature": 0.3, "max_output_tokens": 256},
        )
        content = (resp.text or "").strip()
        return _parse_and_normalize(content, user_text)
    except Exception:
        return _fallback_intent(user_text)


def _parse_and_normalize(content: str, user_text: str) -> Optional[Dict[str, Any]]:
    from intent_parser import parse_intent_response, normalize_intent
    parsed = parse_intent_response(content)
    if parsed:
        return normalize_intent(parsed)
    return _fallback_intent(user_text)


def _fallback_intent(user_text: str) -> Dict[str, Any]:
    """
    Simple heuristic when API is missing or fails: treat as play_song if it looks like "play X" or "play music X".
    """
    lower = user_text.lower().strip()
    # "play music blinding lights" -> song "blinding lights"
    if lower.startswith("play music ") and len(lower) > 11:
        song = user_text[11:].strip()
        return {"intent": "play_song", "song": song, "platform": "youtube_music"}
    # "play blinding lights" -> song "blinding lights"
    if lower.startswith("play ") and len(lower) > 5:
        song = user_text[5:].strip()
        return {"intent": "play_song", "song": song, "platform": "youtube_music"}
    if "volume up" in lower or "increase volume" in lower:
        return {"intent": "volume_up"}
    if "volume down" in lower or "decrease volume" in lower:
        return {"intent": "volume_down"}
    if "pause" in lower or "stop" in lower:
        return {"intent": "pause_media"}
    if "resume" in lower or "play" in lower and "song" not in lower:
        return {"intent": "play_media"}
    return {"intent": "unknown", "query": user_text}
