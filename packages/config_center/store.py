from __future__ import annotations

from pathlib import Path
from typing import Any


class ConfigCenter:
    def __init__(self, path: str = "configs/database.toml") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_default()

    def _write_default(self) -> None:
        self.path.write_text(
            """# Database config\n\n[database]\ndriver = \"sqlite\"\nsqlite_path = \"data/state.db\"\npostgres_dsn = \"postgresql://postgres:postgres@localhost:5432/personal_ai_assistant\"\n\n[vector]\nprovider = \"pgvector\"\nembedding_dim = 1536\n\n[metrics]\nbackend = \"sqlite\"\nclickhouse_dsn = \"clickhouse://default:@localhost:8123/default\"\n\n[voice]\nprovider = \"mock\"\ndefault_voice_id = \"airi-cn\"\nbase_url = \"http://127.0.0.1:9000\"\napi_key = \"\"\nmodel = \"general\"\ntimeout_ms = 8000\ntranscribe_path = \"/asr/transcribe\"\nspeak_path = \"/tts/speak\"\nhealth_path = \"/health\"\n""",
            encoding="utf-8",
        )

    def load(self) -> dict[str, Any]:
        sections: dict[str, dict[str, Any]] = {}
        current = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("[") and s.endswith("]"):
                current = s[1:-1].strip()
                sections.setdefault(current, {})
                continue
            if "=" not in s or current is None:
                continue
            k, v = s.split("=", 1)
            key = k.strip()
            val_raw = v.strip()
            val: Any
            if val_raw.startswith('"') and val_raw.endswith('"'):
                val = val_raw.strip('"')
            elif val_raw.isdigit():
                val = int(val_raw)
            else:
                val = val_raw
            sections[current][key] = val

        return {
            "database": sections.get("database", {}),
            "vector": sections.get("vector", {}),
            "metrics": sections.get("metrics", {}),
            "voice": sections.get("voice", {}),
        }

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        current = self.load()
        for sec in ["database", "vector", "metrics", "voice"]:
            if sec in data and isinstance(data[sec], dict):
                current.setdefault(sec, {}).update(data[sec])

        db = current["database"]
        vec = current["vector"]
        met = current["metrics"]
        voice = current["voice"]

        content = (
            "# Database config\n\n"
            "[database]\n"
            f"driver = \"{db.get('driver', 'sqlite')}\"\n"
            f"sqlite_path = \"{db.get('sqlite_path', 'data/state.db')}\"\n"
            f"postgres_dsn = \"{db.get('postgres_dsn', '')}\"\n\n"
            "[vector]\n"
            f"provider = \"{vec.get('provider', 'pgvector')}\"\n"
            f"embedding_dim = {int(vec.get('embedding_dim', 1536))}\n\n"
            "[metrics]\n"
            f"backend = \"{met.get('backend', 'sqlite')}\"\n"
            f"clickhouse_dsn = \"{met.get('clickhouse_dsn', '')}\"\n\n"
            "[voice]\n"
            f"provider = \"{voice.get('provider', 'mock')}\"\n"
            f"default_voice_id = \"{voice.get('default_voice_id', 'airi-cn')}\"\n"
            f"base_url = \"{voice.get('base_url', 'http://127.0.0.1:9000')}\"\n"
            f"api_key = \"{voice.get('api_key', '')}\"\n"
            f"model = \"{voice.get('model', 'general')}\"\n"
            f"timeout_ms = {int(voice.get('timeout_ms', 8000))}\n"
            f"transcribe_path = \"{voice.get('transcribe_path', '/asr/transcribe')}\"\n"
            f"speak_path = \"{voice.get('speak_path', '/tts/speak')}\"\n"
            f"health_path = \"{voice.get('health_path', '/health')}\"\n"
        )

        self.path.write_text(content, encoding="utf-8")
        return current
