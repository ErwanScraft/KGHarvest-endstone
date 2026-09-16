from pathlib import Path

import yaml


class ConfigManager:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.path = Path(plugin.data_folder) / "config.yml"

        self._ensure_config()

        with self.path.open("r", encoding="utf-8") as file:
            self.data = yaml.safe_load(file) or {}

    def _ensure_config(self) -> None:
        if self.path.exists():
            return

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        default_config = {
            "tree_capitator": {
                "enabled": True,
                "require_sneaking": True,
                "max_blocks": 32,
            }
        }

        with self.path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                default_config,
                file,
                sort_keys=False,
            )

    def get(self, path: str, default=None):
        value = self.data

        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                return default

            value = value[key]

        return value