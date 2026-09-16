from endstone.event import BlockBreakEvent, event_handler
from endstone.plugin import Plugin

from .features.tree_capitator.handler import TreeCapitatorHandler
from .utils.config import ConfigManager
from .utils.messages import KGHarvestMessages


class KGHarvestPlugin(Plugin):
    api_version = "0.11"

    name = "KGHarvest"
    version = "0.1.0"
    description = "Harvesting enhancements for KG Survival."
    authors = ["ErwanScraft"]
    prefix = "KGHarvest"

    permissions = {
        "kgharvest.treecapitator": {
            "description": "Allows the player to use Tree Capitator.",
            "default": False,
        }
    }

    def on_enable(self) -> None:
        self.config_manager = ConfigManager(self)
        self.messages = KGHarvestMessages(self)

        self.tree_capitator = TreeCapitatorHandler(
            self,
            self.config_manager,
            self.messages,
        )

        self.register_events(self)

        indicator_interval = max(
            1,
            int(
                self.config_manager.get(
                    "tree_capitator.indicator.interval",
                    5,
                )
            ),
        )

        self.server.scheduler.run_task(
            self,
            self._update_tree_capitator_indicator,
            delay=1,
            period=indicator_interval,
        )

        self.logger.info(
            f"{self.name} v{self.version} enabled."
        )

    def _update_tree_capitator_indicator(self) -> None:
        for player in self.server.online_players:
            self.tree_capitator.update_indicator(
                player
            )

    @event_handler(ignore_cancelled=True)
    def on_block_break(
        self,
        event: BlockBreakEvent,
    ) -> None:
        self.tree_capitator.handle(event)