from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TranscribeResult:
    text: str
    language: str
    confidence: float


@dataclass
class SpeakResult:
    voice_id: str
    speed: float
    text: str
    status: str
    audio_url: str | None


@dataclass
class VoiceHealth:
    ok: bool
    provider: str
    detail: str = ""


class VoiceProvider(Protocol):
    name: str

    def transcribe(self, text: str, language: str = "zh-CN") -> TranscribeResult:
        ...

    def speak(self, text: str, voice_id: str, speed: float = 1.0) -> SpeakResult:
        ...

    def healthcheck(self) -> VoiceHealth:
        ...

