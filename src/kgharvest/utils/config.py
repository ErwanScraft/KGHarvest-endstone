from pathlib import Path
from shutil import copyfile

import yaml


class ConfigManager:
    def __init__(self, plugin) -> None:
        self.plugin = plugin
        self.path = Path(plugin.data_folder) / "config.yml"

        self._ensure_config()
        self._load()

    def _ensure_config(self) -> None:
        if self.path.exists():
            return

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        resource_path = (
            Path(self.plugin.data_folder).parent
            / "resources"
            / "config.yml"
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
                f"Failed to load config.yml: {error}"
            )
            self.data = {}

    def get(self, path: str, default=None):
        value = self.data

        for key in path.split("."):
            if not isinstance(value, dict):
                return default

            if key not in value:
                return default

            value = value[key]

        return value

    def get_int(
        self,
        path: str,
        default: int,
    ) -> int:
        value = self.get(
            path,
            default,
        )

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    def get_float(
        self,
        path: str,
        default: float,
    ) -> float:
        value = self.get(
            path,
            default,
        )

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    def get_bool(
        self,
        path: str,
        default: bool,
    ) -> bool:
        value = self.get(
            path,
            default,
        )

        if isinstance(value, bool):
            return value

        return default