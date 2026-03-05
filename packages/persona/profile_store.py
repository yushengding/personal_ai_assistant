from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class PersonaProfile:
    name: str = "Airi-lite"
    style: str = "friendly"
    tone: str = "concise"
    language: str = "zh-CN"
    voice_id: str = "default"
    avatar_theme: str = "classic"
    updated_at: float = 0.0


class PersonaStore:
    def __init__(self, path: str = "data/persona_profile.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(PersonaProfile())

    def load(self) -> PersonaProfile:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return PersonaProfile(**data)

    def save(self, profile: PersonaProfile | dict[str, Any]) -> PersonaProfile:
        if isinstance(profile, dict):
            merged = asdict(self.load())
            merged.update(profile)
            merged["updated_at"] = time.time()
            p = PersonaProfile(**merged)
        else:
            p = profile
            p.updated_at = time.time()
        self.path.write_text(json.dumps(asdict(p), ensure_ascii=False, indent=2), encoding="utf-8")
        return p

