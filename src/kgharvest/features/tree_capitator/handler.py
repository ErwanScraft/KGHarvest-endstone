import random

from endstone.event import BlockBreakEvent
from endstone.inventory import ItemStack

from .animation import TreeCapitatorAnimation
from .detector import TreeDetector
from .effects import TreeCapitatorEffects


class TreeCapitatorHandler:
    PERMISSION = "kgharvest.treecapitator"

    def __init__(
        self,
        plugin,
        config,
        messages,
    ) -> None:
        self.plugin = plugin
        self.config = config
        self.messages = messages

        self.detector = TreeDetector(config)
        self.effects = TreeCapitatorEffects(config)

        self.active_players = set()

        self.animation = TreeCapitatorAnimation(
            plugin,
            config,
            self._process_log,
            self._process_leaf,
            self._tool_is_valid,
            self._finish_harvest,
        )

    def handle(self, event: BlockBreakEvent) -> None:
        player = event.player
        block = event.block

        if not self.config.get_bool(
            "tree_capitator.enabled",
            True,
        ):
            return

        if not player.has_permission(self.PERMISSION):
            return

        if (
            self.config.get_bool(
                "tree_capitator.require_sneaking",
                True,
            )
            and not player.is_sneaking
        ):
            return

        player_id = str(player.unique_id)

        if player_id in self.active_players:
            return

        item = player.inventory.item_in_main_hand

        if not self.detector.is_axe(item):
            return

        if not self.detector.is_log(block):
            return

        logs = self.detector.find_connected_logs(
            block,
        )

        if not logs:
            return

        leaves = self.detector.find_tree_leaves(
            logs,
            block,
        )

        self.active_players.add(player_id)

        state = {
            "player": player,
            "logs": list(logs),
            "leaves": list(leaves),
            "log_index": 0,
            "leaf_index": 0,
            "sound_counter": 0,
            "active_players": self.active_players,
            "active": True,
        }

        self.plugin.logger.debug(
            f"TreeCapitator player={player.name} "
            f"logs={len(logs) + 1} "
            f"leaves={len(leaves)}"
        )

        self.animation.start(state)

    def update_indicator(self, player) -> None:
        if not self.config.get_bool(
            "tree_capitator.indicator.enabled",
            True,
        ):
            return
    
        if not player.has_permission(self.PERMISSION):
            return
    
        if not player.is_sneaking:
            return
    
        item = player.inventory.item_in_main_hand
    
        if not self.detector.is_axe(item):
            return
    
        message = self.messages.get(
            "tree_capitator.active",
            "",
        )
    
        if not message:
            return
    
        player.send_tip(message)

    def _process_log(
        self,
        state,
        block,
    ) -> bool:
        player = state["player"]

        log_type = self.detector.type_id(
            block.type,
        )

        if not self.detector.is_log(block):
            return True

        state["sound_counter"] = (
            self.effects.play_log_effect(
                player,
                block,
                state["sound_counter"],
            )
        )

        block.set_type(
            "minecraft:air",
            apply_physics=False,
        )

        self._give_item(
            player,
            log_type,
            1,
            block,
        )

        # The original block broken by the player
        # is already handled by vanilla durability.
        # Only additional logs consume extra durability.
        return self._damage_tool(player)

    def _process_leaf(
        self,
        state,
        block,
    ) -> None:
        player = state["player"]

        if not self.detector.is_leaf(block):
            return

        leaf_type = self.detector.type_id(
            block.type,
        )

        self.effects.play_leaf_effect(
            player,
            block,
        )

        block.set_type(
            "minecraft:air",
            apply_physics=False,
        )

        item = player.inventory.item_in_main_hand

        silk_touch = self._has_enchantment(
            item,
            "silk_touch",
        )

        fortune_level = self._get_enchantment_level(
            item,
            "fortune",
        )

        if silk_touch:
            self._give_item(
                player,
                leaf_type,
                1,
                block,
            )
            return

        self._process_leaf_drops(
            player,
            block,
            leaf_type,
            fortune_level,
        )

    def _damage_tool(self, player) -> bool:
        item = player.inventory.item_in_main_hand
    
        if item is None:
            return False
    
        meta = item.item_meta
    
        if meta is None:
            return True
    
        if meta.is_unbreakable:
            return True
    
        unbreaking_level = self._get_enchantment_level(
            item,
            "unbreaking",
        )
    
        if unbreaking_level > 0:
            if random.random() >= 1.0 / (
                unbreaking_level + 1
            ):
                return True
    
        max_durability = int(
            item.type.max_durability
        )
    
        if max_durability <= 0:
            return True
    
        current_damage = int(
            meta.damage
        )
    
        new_damage = current_damage + 1
    
        if new_damage >= max_durability:
            player.inventory.item_in_main_hand = None
    
            message = self.messages.prefixed(
                "tree_capitator.axe_broken",
                "§cYour axe broke.",
            )
    
            if message:
                player.send_message(message)
    
            return False
    
        meta.damage = new_damage
        item.set_item_meta(meta)
    
        # ItemStack/ItemMeta are handled as objects/copies.
        # Re-apply the modified stack to the player's inventory.
        player.inventory.item_in_main_hand = item
    
        return True

    def _tool_is_valid(self, player) -> bool:
        item = player.inventory.item_in_main_hand

        return self.detector.is_axe(item)

    def _process_leaf_drops(
        self,
        player,
        leaf,
        leaf_type,
        fortune_level,
    ) -> None:
        sapling = self.detector.LEAF_TO_SAPLING.get(
            leaf_type,
        )

        if sapling is None:
            return

        sapling_chance = min(
            1.0,
            0.05 + fortune_level * 0.025,
        )

        if random.random() <= sapling_chance:
            self._give_item(
                player,
                sapling,
                1,
                leaf,
            )

        stick_chance = min(
            1.0,
            0.02 + fortune_level * 0.01,
        )

        if random.random() <= stick_chance:
            self._give_item(
                player,
                "minecraft:stick",
                1,
                leaf,
            )

        if leaf_type == "minecraft:oak_leaves":
            apple_chance = min(
                1.0,
                0.005 + fortune_level * 0.0025,
            )

            if random.random() <= apple_chance:
                self._give_item(
                    player,
                    "minecraft:apple",
                    1,
                    leaf,
                )

    def _give_item(
        self,
        player,
        item_type,
        amount,
        source_block,
    ) -> None:
        stack = ItemStack(
            item_type,
            amount,
        )

        leftovers = player.inventory.add_item(
            stack,
        )

        if not leftovers:
            return

        for leftover in leftovers.values():
            source_block.dimension.drop_item(
                source_block.location,
                leftover,
            )

    def _finish_harvest(self, state) -> None:
        if not state["active"]:
            return
    
        state["active"] = False
    
        player_id = str(
            state["player"].unique_id
        )
    
        self.active_players.discard(
            player_id,
        )

    @staticmethod
    def _get_enchantment_level(
        item,
        enchantment,
    ) -> int:
        if item is None:
            return 0

        try:
            return item.item_meta.get_enchant_level(
                enchantment,
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _has_enchantment(
        item,
        enchantment,
    ) -> bool:
        if item is None:
            return False

        try:
            return item.item_meta.has_enchant(
                enchantment,
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return False