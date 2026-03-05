from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from packages.plugins.models import LoadedPlugin, PluginManifest


class PluginManager:
    def __init__(self, plugins_root: str = "plugins") -> None:
        self.plugins_root = Path(plugins_root)
        self.plugins_root.mkdir(parents=True, exist_ok=True)
        self.plugins: dict[str, LoadedPlugin] = {}
        self.modules: dict[str, object] = {}

    def reload_all(self) -> dict[str, LoadedPlugin]:
        self.plugins.clear()
        self.modules.clear()

        for d in sorted(self.plugins_root.iterdir()):
            if not d.is_dir():
                continue
            try:
                loaded = self._load_one(d)
                self.plugins[loaded.manifest.name] = loaded
            except Exception as exc:
                name = d.name
                self.plugins[name] = LoadedPlugin(
                    manifest=PluginManifest(name=name, version="0.0.0", entry=""),
                    plugin_dir=str(d),
                    status="error",
                    health="failed",
                    error=str(exc),
                )
        return self.plugins

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.manifest.name,
                "version": p.manifest.version,
                "entry": p.manifest.entry,
                "capabilities": p.manifest.capabilities,
                "required_scopes": p.manifest.required_scopes,
                "risk_level": p.manifest.risk_level,
                "status": p.status,
                "health": p.health,
                "error": p.error,
                "plugin_dir": p.plugin_dir,
            }
            for p in self.plugins.values()
        ]

    def activate(self, name: str) -> dict:
        plugin = self._require(name)
        module = self.modules.get(name)
        if module and hasattr(module, "activate"):
            module.activate()
        plugin.status = "active"
        return {"name": name, "status": plugin.status}

    def deactivate(self, name: str) -> dict:
        plugin = self._require(name)
        module = self.modules.get(name)
        if module and hasattr(module, "deactivate"):
            module.deactivate()
        plugin.status = "inactive"
        return {"name": name, "status": plugin.status}

    def healthcheck(self, name: str) -> dict:
        plugin = self._require(name)
        module = self.modules.get(name)
        result = {"ok": True}
        if module and hasattr(module, "healthcheck"):
            result = module.healthcheck()
        plugin.health = "ok" if result.get("ok", False) else "failed"
        return {"name": name, "health": plugin.health, "details": result}

    def _load_one(self, plugin_dir: Path) -> LoadedPlugin:
        manifest_path = plugin_dir / "manifest.json"
        if not manifest_path.exists():
            raise ValueError("manifest.json not found")

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = PluginManifest.from_dict(data)

        entry_path = plugin_dir / manifest.entry
        if not entry_path.exists():
            raise ValueError(f"entry not found: {manifest.entry}")

        module_name = f"pai_plugin_{manifest.name}"
        spec = importlib.util.spec_from_file_location(module_name, entry_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"failed to create module spec for {entry_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        self.modules[manifest.name] = module

        loaded = LoadedPlugin(manifest=manifest, plugin_dir=str(plugin_dir), status="loaded")
        if hasattr(module, "healthcheck"):
            try:
                h = module.healthcheck()
                loaded.health = "ok" if isinstance(h, dict) and h.get("ok", False) else "failed"
            except Exception as exc:
                loaded.health = "failed"
                loaded.error = str(exc)
        else:
            loaded.health = "unknown"

        return loaded

    def _require(self, name: str) -> LoadedPlugin:
        if name not in self.plugins:
            raise ValueError("plugin not found")
        return self.plugins[name]

