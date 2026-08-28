import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "prefix"                : "!",
    "timeout_seconds"       : 10,
    "auto_refresh_seconds"  : 300,
    "auto_refresh_channel"  : None,
}

CONFIG_PATH = Path("config.json")


class ConfigManager:

    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            self._save(DEFAULT_CONFIG)
            return dict(DEFAULT_CONFIG)
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data

    def _save(self, data: dict) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str, fallback=None):
        return self.data.get(key, fallback)

    def set(self, key: str, value) -> None:
        self.data[key] = value
        self._save(self.data)

    @property
    def token(self) -> str:
        # Read token from environment variable only — never hardcoded
        return os.environ.get("BOT_TOKEN", "")
