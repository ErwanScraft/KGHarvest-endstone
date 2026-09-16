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
                "limits": {
                    "logs": 32,
                    "leaves": 128,
                },
                "animation": {
                    "enabled": True,
                    "delay": 1,
                    "logs_per_tick": 1,
                    "leaves_per_tick": 4,
                },
                "indicator": {
                    "enabled": True,
                    "interval": 5,
                },
                "effects": {
                    "enabled": True,
                    "particles": {
                        "log_bottom": "kgserver:break1",
                        "log_top": "kgserver:break2",
                        "leaf": "kgserver:break1",
                        "step_y": 0.2,
                        "bottom": {
                            "start_y": -0.9,
                            "end_y": -0.1,
                        },
                        "top": {
                            "start_y": 0.1,
                            "end_y": 0.9,
                        },
                    },
                    "sound": {
                        "name": "kgserver.break.log",
                        "volume": 0.75,
                        "pitch": 1.0,
                        "interval": 2,
                    },
                },
            }
        }

        with self.path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                default_config,
                file,
                sort_keys=False,
                allow_unicode=True,
            )

    def get(self, path: str, default=None):
        value = self.data

        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                return default

            value = value[key]

        return value

    def get_int(self, path: str, default: int) -> int:
        try:
            return int(self.get(path, default))
        except (TypeError, ValueError):
            return default

    def get_float(self, path: str, default: float) -> float:
        try:
            return float(self.get(path, default))
        except (TypeError, ValueError):
            return default

    def get_bool(self, path: str, default: bool) -> bool:
        value = self.get(path, default)

        if isinstance(value, bool):
            return value

        return default