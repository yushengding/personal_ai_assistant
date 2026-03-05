from __future__ import annotations

from packages.voice.types import SpeakResult, TranscribeResult, VoiceHealth, VoiceProvider


class DisabledVoiceProvider(VoiceProvider):
    name = "disabled"

    def transcribe(self, text: str, language: str = "zh-CN") -> TranscribeResult:
        return TranscribeResult(text=text, language=language, confidence=0.0)

    def speak(self, text: str, voice_id: str, speed: float = 1.0) -> SpeakResult:
        return SpeakResult(voice_id=voice_id, speed=speed, text=text, status="disabled", audio_url=None)

    def healthcheck(self) -> VoiceHealth:
        return VoiceHealth(ok=False, provider=self.name, detail="voice feature is disabled by config")
