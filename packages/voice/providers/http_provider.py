from __future__ import annotations

import json
from urllib import error, request

from packages.voice.types import SpeakResult, TranscribeResult, VoiceHealth, VoiceProvider


class HttpVoiceProvider(VoiceProvider):
    name = "http"

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        model: str = "",
        timeout_ms: int = 8000,
        transcribe_path: str = "/asr/transcribe",
        speak_path: str = "/tts/speak",
        health_path: str = "/health",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = max(timeout_ms, 1000) / 1000.0
        self.transcribe_path = transcribe_path
        self.speak_path = speak_path
        self.health_path = health_path

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = request.Request(url=url, data=body, method="POST", headers=headers)
        with request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = request.Request(url=url, method="GET", headers=headers)
        with request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def transcribe(self, text: str, language: str = "zh-CN") -> TranscribeResult:
        try:
            res = self._post(
                self.transcribe_path,
                {"text": text, "language": language, "model": self.model},
            )
            return TranscribeResult(
                text=str(res.get("text", text)),
                language=str(res.get("language", language)),
                confidence=float(res.get("confidence", 0.8)),
            )
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return TranscribeResult(text=text, language=language, confidence=0.0)

    def speak(self, text: str, voice_id: str, speed: float = 1.0) -> SpeakResult:
        try:
            res = self._post(
                self.speak_path,
                {"text": text, "voice_id": voice_id, "speed": speed, "model": self.model},
            )
            return SpeakResult(
                voice_id=str(res.get("voice_id", voice_id)),
                speed=float(res.get("speed", speed)),
                text=str(res.get("text", text)),
                status=str(res.get("status", "ok")),
                audio_url=res.get("audio_url"),
            )
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return SpeakResult(voice_id=voice_id, speed=speed, text=text, status="failed", audio_url=None)

    def healthcheck(self) -> VoiceHealth:
        if not self.base_url:
            return VoiceHealth(ok=False, provider=self.name, detail="base_url is empty")
        try:
            res = self._get(self.health_path)
            ok = bool(res.get("ok", True))
            return VoiceHealth(ok=ok, provider=self.name, detail=str(res.get("detail", "http provider")))
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            return VoiceHealth(ok=False, provider=self.name, detail=f"http unavailable: {exc}")
