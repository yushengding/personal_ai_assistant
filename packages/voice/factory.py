from __future__ import annotations

import os
from pathlib import Path
import tomllib
from typing import Any

from packages.voice.providers.disabled_provider import DisabledVoiceProvider
from packages.voice.providers.http_provider import HttpVoiceProvider
from packages.voice.providers.mock_provider import MockVoiceProvider
from packages.voice.types import VoiceProvider

SUPPORTED_VOICE_PROVIDERS = ("mock", "disabled", "http")


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as fp:
        return tomllib.load(fp)


def create_voice_provider() -> VoiceProvider:
    cfg = _load_toml(Path(os.getenv("PAI_DB_CONFIG", "configs/database.toml")))
    voice_cfg: dict[str, Any] = cfg.get("voice", {}) if isinstance(cfg, dict) else {}
    provider = os.getenv("PAI_VOICE_PROVIDER", str(voice_cfg.get("provider", "mock"))).lower()

    if provider == "mock":
        return MockVoiceProvider()
    if provider == "disabled":
        return DisabledVoiceProvider()
    if provider == "http":
        return HttpVoiceProvider(
            base_url=str(voice_cfg.get("base_url", "")),
            api_key=str(voice_cfg.get("api_key", "")),
            model=str(voice_cfg.get("model", "")),
            timeout_ms=int(voice_cfg.get("timeout_ms", 8000)),
            transcribe_path=str(voice_cfg.get("transcribe_path", "/asr/transcribe")),
            speak_path=str(voice_cfg.get("speak_path", "/tts/speak")),
            health_path=str(voice_cfg.get("health_path", "/health")),
        )

    return MockVoiceProvider()


def list_voice_providers() -> list[str]:
    return list(SUPPORTED_VOICE_PROVIDERS)
