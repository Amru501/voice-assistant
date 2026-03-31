"""
Jarvis Assistant - Intent Parser
Parses AI response text into structured JSON for automation.
"""

import json
import re
from typing import Any, Dict, Optional


def parse_intent_response(raw: str) -> Optional[Dict[str, Any]]:
    """
    Parse AI response into structured intent JSON.
    Expects raw to contain a JSON object (possibly inside markdown code block).
    Returns dict or None if parsing fails.
    """
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    # Try to extract JSON from markdown code block if present
    code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if code_match:
        raw = code_match.group(1).strip()
    # Find first { ... } block
    start = raw.find("{")
    if start == -1:
        return None
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def normalize_intent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure intent has expected keys: intent, and optional song, platform, app, action, etc.
    """
    out = {"intent": (data.get("intent") or data.get("action") or "unknown").strip().lower()}
    if "song" in data and data["song"]:
        out["song"] = str(data["song"]).strip()
    if "platform" in data and data["platform"]:
        out["platform"] = str(data["platform"]).strip().lower()
    if "app" in data and data["app"]:
        out["app"] = str(data["app"]).strip()
    if "action" in data and data["action"]:
        out["action"] = str(data["action"]).strip().lower()
    if "query" in data and data["query"]:
        out["query"] = str(data["query"]).strip()
    if "volume" in data:
        try:
            out["volume"] = int(data["volume"])
        except (TypeError, ValueError):
            pass
    # Copy any other keys as-is for extensibility
    for k, v in data.items():
        if k not in out and v is not None:
            out[k] = v
    return out
