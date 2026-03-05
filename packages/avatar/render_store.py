from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class AvatarRenderConfig:
    renderer: str = "live2d"  # live2d | vrm
    model_path: str = "assets/avatar/default.model3.json"
    idle_animation: str = "idle"
    talk_animation: str = "talk"
    emotion_map: dict[str, str] | None = None


class AvatarRenderStore:
    def __init__(self, path: str = "data/avatar_render_config.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(AvatarRenderConfig())

    def load(self) -> AvatarRenderConfig:
        import json

        data = json.loads(self.path.read_text(encoding="utf-8"))
        return AvatarRenderConfig(**data)

    def save(self, cfg: AvatarRenderConfig | dict[str, Any]) -> AvatarRenderConfig:
        import json

        if isinstance(cfg, dict):
            current = asdict(self.load())
            current.update(cfg)
            c = AvatarRenderConfig(**current)
        else:
            c = cfg
        if c.emotion_map is None:
            c.emotion_map = {
                "idle": "neutral",
                "running": "focused",
                "waiting_decision": "questioning",
                "completed": "happy",
                "failed": "sad",
            }
        self.path.write_text(json.dumps(asdict(c), ensure_ascii=False, indent=2), encoding="utf-8")
        return c

