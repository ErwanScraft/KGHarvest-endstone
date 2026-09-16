from pathlib import Path

import yaml


class KGHarvestMessages:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.path = Path(plugin.data_folder) / "message.yml"

        self._ensure_messages()

        with self.path.open("r", encoding="utf-8") as file:
            self.data = yaml.safe_load(file) or {}

    def _ensure_messages(self) -> None:
        if self.path.exists():
            return

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        default_messages = {
            "prefix": "<green>KGHarvest</green> <dark_gray>»</dark_gray>",
            "tree_capitator": {
                "harvested": "<green>Harvested <white>{amount}</white> logs.</green>",
                "limit_reached": (
                    "<yellow>Tree Capitator limit reached: "
                    "<white>{limit}</white> logs.</yellow>"
                ),
            },
        }

        with self.path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                default_messages,
                file,
                sort_keys=False,
                allow_unicode=True,
            )

    def get(self, path: str, default: str = "") -> str:
        value = self.data

        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                return default

            value = value[key]

        return value