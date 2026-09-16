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
            "prefix": "§aKGHarvest §8»",
            "tree_capitator": {
                "active": "§a● §fTree Capitator §aActive",
                "harvested": "§aHarvested §f{amount} §alog(s).",
                "limit_reached": (
                    "§eTree Capitator limit reached: "
                    "§f{limit} §alog(s)."
                ),
                "axe_broken": "§cYour axe broke.",
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

        if not isinstance(value, str):
            return default

        return value

    def format(self, path: str, default: str = "", **values) -> str:
        message = self.get(path, default)

        if not message:
            return ""

        try:
            return message.format(**values)
        except (KeyError, ValueError):
            return message

    def prefixed(self, path: str, default: str = "", **values) -> str:
        prefix = self.get("prefix", "")
        message = self.format(
            path,
            default,
            **values,
        )

        if not message:
            return prefix

        if not prefix:
            return message

        return f"{prefix} §r{message}"