from pathlib import Path
from shutil import copyfile

import yaml


class KGHarvestMessages:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.path = Path(plugin.data_folder) / "message.yml"

        self._ensure_messages()
        self._load()

    def _ensure_messages(self) -> None:
        if self.path.exists():
            return

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        resource_path = (
            Path(self.plugin.data_folder).parent
            / "resources"
            / "message.yml"
        )

        if resource_path.exists():
            copyfile(
                resource_path,
                self.path,
            )
            return

        self.path.touch()

    def _load(self) -> None:
        try:
            with self.path.open(
                "r",
                encoding="utf-8",
            ) as file:
                self.data = yaml.safe_load(file) or {}
        except (
            OSError,
            yaml.YAMLError,
        ) as error:
            self.plugin.logger.error(
                f"Failed to load message.yml: {error}"
            )
            self.data = {}

    def get(
        self,
        path: str,
        default: str = "",
    ) -> str:
        value = self.data

        for key in path.split("."):
            if not isinstance(value, dict):
                return default

            if key not in value:
                return default

            value = value[key]

        if not isinstance(value, str):
            return default

        return value

    def format(
        self,
        path: str,
        default: str = "",
        **values,
    ) -> str:
        message = self.get(
            path,
            default,
        )

        if not message:
            return ""

        try:
            return message.format(
                **values,
            )
        except (
            KeyError,
            ValueError,
        ):
            return message

    def prefixed(
        self,
        path: str,
        default: str = "",
        **values,
    ) -> str:
        prefix = self.get(
            "prefix",
            "",
        )

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