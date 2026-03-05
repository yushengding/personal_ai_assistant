from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass
class UpgradeState:
    mode: str = "idle"  # idle|prepared|promoted|rolled_back
    active_slot: str = "active"
    candidate_slot: str = "candidate"
    target_version: str | None = None
    last_good_version: str = "v0.2.0"
    current_version: str = "v0.2.0"
    last_action_at: float = 0.0
    last_error: str | None = None


class UpgradeManager:
    def __init__(self, state_path: str = "data/upgrade_state.json") -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_or_init()

    def _load_or_init(self) -> UpgradeState:
        if not self.state_path.exists():
            state = UpgradeState(last_action_at=time.time())
            self._save(state)
            return state
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return UpgradeState(**data)

    def _save(self, state: UpgradeState) -> None:
        self.state_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")

    def status(self) -> dict:
        return asdict(self.state)

    def prepare(self, target_version: str) -> dict:
        self.state.mode = "prepared"
        self.state.target_version = target_version
        self.state.last_action_at = time.time()
        self.state.last_error = None
        self._save(self.state)
        return self.status()

    def healthcheck(self, checks: dict[str, Callable[[], dict]]) -> dict:
        results: dict[str, dict] = {}
        ok = True
        err_msg = None

        for name, fn in checks.items():
            try:
                res = fn()
                res_ok = bool(res.get("ok", False))
                ok = ok and res_ok
                results[name] = res
                if not res_ok and err_msg is None:
                    err_msg = f"check failed: {name}"
            except Exception as exc:
                ok = False
                results[name] = {"ok": False, "error": str(exc)}
                if err_msg is None:
                    err_msg = f"check exception: {name}"

        self.state.last_action_at = time.time()
        self.state.last_error = err_msg
        self._save(self.state)
        return {"ok": ok, "checks": results, "state": self.status()}

    def promote(self) -> dict:
        if self.state.mode != "prepared":
            raise ValueError("upgrade not prepared")
        self.state.mode = "promoted"
        self.state.last_good_version = self.state.current_version
        if self.state.target_version:
            self.state.current_version = self.state.target_version
        self.state.last_action_at = time.time()
        self.state.last_error = None
        self._save(self.state)
        return self.status()

    def rollback(self, reason: str = "manual") -> dict:
        self.state.mode = "rolled_back"
        self.state.current_version = self.state.last_good_version
        self.state.target_version = None
        self.state.last_action_at = time.time()
        self.state.last_error = reason
        self._save(self.state)
        return self.status()

