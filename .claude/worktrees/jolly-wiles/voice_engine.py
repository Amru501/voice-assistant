"""
Jarvis Assistant - Voice Engine
Handles speech-to-text (microphone) and text-to-speech (Jarvis-like voice).
"""

import threading
import queue
import time
from typing import Optional

import speech_recognition as sr
import pyttsx3

import config


class VoiceEngine:
    """
    Listens to microphone and converts speech to text.
    Speaks responses using pyttsx3 with a calm, intelligent tone.
    """

    def __init__(self, on_phrase_callback=None):
        """
        Args:
            on_phrase_callback: Optional callable(text: str) called when a phrase is recognized.
        """
        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone()
        self._on_phrase = on_phrase_callback
        self._listening = False
        self._listen_thread = None
        self._phrase_queue = queue.Queue()
        # TTS engine (lazy init on first speak)
        self._tts_engine = None
        self._tts_lock = threading.Lock()
        # Adjust for ambient noise once
        self._calibrated = False

    def _get_tts_engine(self):
        """Lazy-initialize and return pyttsx3 engine with Jarvis-like settings."""
        with self._tts_lock:
            if self._tts_engine is None:
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty("rate", config.TTS_RATE)
                self._tts_engine.setProperty("volume", config.TTS_VOLUME)
                # Prefer a clear, calm voice if available
                voices = self._tts_engine.getProperty("voices")
                if voices and len(voices) > config.TTS_VOICE_INDEX:
                    self._tts_engine.setProperty("voice", voices[config.TTS_VOICE_INDEX].id)
            return self._tts_engine

    def speak(self, text: str, block: bool = True) -> None:
        """
        Speak text in a calm, minimal Jarvis style.
        Optionally normalizes short responses (e.g. "Done.", "Standing by.").
        """
        if not text or not text.strip():
            return
        # Normalize: single sentence, no trailing period in middle
        text = text.strip()
        if not text.endswith((".", "!", "?")):
            text += "."
        with self._tts_lock:
            engine = self._get_tts_engine()
            engine.say(text)
            if block:
                engine.runAndWait()

    def _listen_loop(self) -> None:
        """Background loop: listen to mic, push recognized phrases to callback or queue."""
        with self._microphone as source:
            if not self._calibrated:
                try:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                except Exception:
                    pass
                self._calibrated = True
            while self._listening:
                try:
                    self._recognizer.energy_threshold = config.ENERGY_THRESHOLD
                    audio = self._recognizer.listen(
                        source,
                        timeout=config.PHRASE_TIMEOUT,
                        phrase_time_limit=10,
                    )
                    text = self._recognizer.recognize_google(audio, language="en-US")
                    text = (text or "").strip()
                    if text:
                        if self._on_phrase:
                            self._on_phrase(text)
                        self._phrase_queue.put(text)
                except sr.UnknownValueError:
                    try:
                        from debug_log import log
                        log("Speech: could not understand (UnknownValueError)")
                    except Exception:
                        pass
                    continue
                except sr.RequestError as e:
                    try:
                        from debug_log import log
                        log(f"Speech: API error (RequestError): {e}")
                    except Exception:
                        pass
                    continue
                except sr.WaitTimeoutError:
                    continue
                except Exception:
                    try:
                        from debug_log import log_exception
                        log_exception()
                    except Exception:
                        pass
                    if self._listening:
                        time.sleep(0.2)
                    continue

    def start_listening(self, on_phrase_callback=None) -> None:
        """Start continuous listening in a background thread."""
        if on_phrase_callback:
            self._on_phrase = on_phrase_callback
        if self._listening:
            return
        self._listening = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop the listening loop."""
        self._listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
            self._listen_thread = None

    def get_phrase(self, timeout: float = 0.5) -> Optional[str]:
        """Get next recognized phrase from queue, or None if none available within timeout."""
        try:
            return self._phrase_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def shutdown(self) -> None:
        """Release TTS and stop listening."""
        self.stop_listening()
        with self._tts_lock:
            if self._tts_engine:
                try:
                    self._tts_engine.stop()
                except Exception:
                    pass
                self._tts_engine = None
