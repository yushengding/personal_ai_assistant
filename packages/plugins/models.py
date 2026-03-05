from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginManifest:
    name: str
    version: str
    entry: str
    capabilities: list[str] = field(default_factory=list)
    required_scopes: list[str] = field(default_factory=list)
    risk_level: str = "safe"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PluginManifest":
        required = ["name", "version", "entry"]
        missing = [k for k in required if k not in data or not data[k]]
        if missing:
            raise ValueError(f"manifest missing required fields: {missing}")

        risk = str(data.get("risk_level", "safe")).lower()
        if risk not in {"safe", "guarded", "restricted"}:
            raise ValueError(f"unsupported risk_level: {risk}")

        return PluginManifest(
            name=str(data["name"]),
            version=str(data["version"]),
            entry=str(data["entry"]),
            capabilities=[str(x) for x in data.get("capabilities", [])],
            required_scopes=[str(x) for x in data.get("required_scopes", [])],
            risk_level=risk,
        )


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    plugin_dir: str
    status: str = "loaded"
    health: str = "unknown"
    error: str | None = None

