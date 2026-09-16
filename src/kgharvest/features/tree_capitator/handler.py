from collections import deque
import random

from endstone.event import BlockBreakEvent
from endstone.inventory import ItemStack


class TreeCapitatorHandler:
    AXE_TYPES = {
        "minecraft:wooden_axe",
        "minecraft:stone_axe",
        "minecraft:iron_axe",
        "minecraft:golden_axe",
        "minecraft:diamond_axe",
        "minecraft:netherite_axe",
    }

    LOG_TYPES = {
        "minecraft:acacia_log",
        "minecraft:birch_log",
        "minecraft:cherry_log",
        "minecraft:crimson_stem",
        "minecraft:dark_oak_log",
        "minecraft:jungle_log",
        "minecraft:mangrove_log",
        "minecraft:oak_log",
        "minecraft:spruce_log",
        "minecraft:warped_stem",
    }

    LEAF_TYPES = {
        "minecraft:acacia_leaves",
        "minecraft:azalea_leaves",
        "minecraft:azalea_leaves_flowered",
        "minecraft:birch_leaves",
        "minecraft:cherry_leaves",
        "minecraft:dark_oak_leaves",
        "minecraft:jungle_leaves",
        "minecraft:mangrove_leaves",
        "minecraft:oak_leaves",
        "minecraft:spruce_leaves",
    }

    LEAF_TO_SAPLING = {
        "minecraft:acacia_leaves": "minecraft:acacia_sapling",
        "minecraft:azalea_leaves": "minecraft:azalea",
        "minecraft:azalea_leaves_flowered": "minecraft:flowering_azalea",
        "minecraft:birch_leaves": "minecraft:birch_sapling",
        "minecraft:cherry_leaves": "minecraft:cherry_sapling",
        "minecraft:dark_oak_leaves": "minecraft:dark_oak_sapling",
        "minecraft:jungle_leaves": "minecraft:jungle_sapling",
        "minecraft:mangrove_leaves": "minecraft:mangrove_propagule",
        "minecraft:oak_leaves": "minecraft:oak_sapling",
        "minecraft:spruce_leaves": "minecraft:spruce_sapling",
    }

    DIRECTIONS = (
        (-1, -1, -1),
        (-1, -1, 0),
        (-1, -1, 1),
        (-1, 0, -1),
        (-1, 0, 0),
        (-1, 0, 1),
        (-1, 1, -1),
        (-1, 1, 0),
        (-1, 1, 1),
        (0, -1, -1),
        (0, -1, 0),
        (0, -1, 1),
        (0, 0, -1),
        (0, 0, 1),
        (0, 1, -1),
        (0, 1, 0),
        (0, 1, 1),
        (1, -1, -1),
        (1, -1, 0),
        (1, -1, 1),
        (1, 0, -1),
        (1, 0, 0),
        (1, 0, 1),
        (1, 1, -1),
        (1, 1, 0),
        (1, 1, 1),
    )

    def __init__(self, plugin, config, messages) -> None:
        self.plugin = plugin
        self.config = config
        self.messages = messages

    def handle(self, event: BlockBreakEvent) -> None:
        player = event.player
        block = event.block

        if not self.config.get("tree_capitator.enabled", True):
            return

        if not player.has_permission("kgharvest.treecapitator"):
            return

        if self.config.get(
            "tree_capitator.require_sneaking",
            True,
        ) and not player.is_sneaking:
            return

        item = player.inventory.item_in_main_hand

        if item is None:
            return

        item_type = self._get_type_id(item.type)

        if item_type not in self.AXE_TYPES:
            return

        block_type = self._get_type_id(block.type)

        if block_type not in self.LOG_TYPES:
            return

        additional_logs = self._find_connected_logs(block)

        if not additional_logs:
            return

        self.plugin.logger.debug(
            f"[DEBUG] ConnectedLogs={len(additional_logs) + 1}"
        )

        self._play_effect(player, block)

        self._process_logs(
            player,
            additional_logs,
        )

        leaves = self._find_tree_leaves(
            additional_logs,
            block,
        )

        self._process_leaves(
            player,
            leaves,
        )

    def _find_connected_logs(self, origin):
        max_blocks = int(
            self.config.get(
                "tree_capitator.max_blocks",
                32,
            )
        )

        if max_blocks <= 1:
            return []

        dimension = origin.dimension

        queue = deque()
        visited = set()
        connected = []

        origin_pos = (
            origin.x,
            origin.y,
            origin.z,
        )

        queue.append(origin_pos)
        visited.add(origin_pos)

        while queue and len(connected) < max_blocks - 1:
            x, y, z = queue.popleft()

            for dx, dy, dz in self.DIRECTIONS:
                position = (
                    x + dx,
                    y + dy,
                    z + dz,
                )

                if position in visited:
                    continue

                visited.add(position)

                block = dimension.get_block_at(
                    position[0],
                    position[1],
                    position[2],
                )

                if self._get_type_id(block.type) not in self.LOG_TYPES:
                    continue

                connected.append(block)
                queue.append(position)

                if len(connected) >= max_blocks - 1:
                    break

        return connected

    def _find_tree_leaves(self, logs, origin):
        max_leaves = int(
            self.config.get(
                "tree_capitator.max_leaves",
                128,
            )
        )

        if max_leaves <= 0:
            return []

        if not logs:
            return []

        dimension = origin.dimension

        queue = deque()
        visited = set()
        leaves = []

        log_positions = set()

        log_blocks = [origin]
        log_blocks.extend(logs)

        for log in log_blocks:
            position = (
                log.x,
                log.y,
                log.z,
            )

            log_positions.add(position)
            queue.append(position)
            visited.add(position)

        while queue and len(leaves) < max_leaves:
            x, y, z = queue.popleft()

            for dx, dy, dz in self.DIRECTIONS:
                position = (
                    x + dx,
                    y + dy,
                    z + dz,
                )

                if position in visited:
                    continue

                visited.add(position)

                block = dimension.get_block_at(
                    position[0],
                    position[1],
                    position[2],
                )

                block_type = self._get_type_id(block.type)

                if block_type in self.LEAF_TYPES:
                    leaves.append(block)
                    queue.append(position)

                    if len(leaves) >= max_leaves:
                        break

                elif block_type in self.LOG_TYPES:
                    # Continue through logs so that leaves connected
                    # to another part of the same tree can be reached.
                    queue.append(position)

        return leaves

    def _process_logs(self, player, logs) -> None:
        for tree_block in logs:
            log_type = self._get_type_id(tree_block.type)

            tree_block.set_type(
                "minecraft:air",
                apply_physics=False,
            )

            self._give_item(
                player,
                log_type,
                1,
                tree_block,
            )

    def _process_leaves(self, player, leaves) -> None:
        item = player.inventory.item_in_main_hand

        silk_touch = self._has_enchantment(
            item,
            "silk_touch",
        )

        fortune_level = self._get_enchantment_level(
            item,
            "fortune",
        )

        for leaf in leaves:
            leaf_type = self._get_type_id(leaf.type)

            leaf.set_type(
                "minecraft:air",
                apply_physics=False,
            )

            if silk_touch:
                self._give_item(
                    player,
                    leaf_type,
                    1,
                    leaf,
                )
                continue

            self._process_leaf_drops(
                player,
                leaf,
                leaf_type,
                fortune_level,
            )

    def _process_leaf_drops(
        self,
        player,
        leaf,
        leaf_type,
        fortune_level,
    ) -> None:
        sapling = self.LEAF_TO_SAPLING.get(leaf_type)

        if sapling is None:
            return

        # Approximation of vanilla-style leaf drops.
        # Fortune increases the chance.
        sapling_chance = min(
            1.0,
            0.05 + (fortune_level * 0.025),
        )

        if random.random() <= sapling_chance:
            self._give_item(
                player,
                sapling,
                1,
                leaf,
            )

        # Standard tree leaves can additionally drop sticks.
        stick_chance = min(
            1.0,
            0.02 + (fortune_level * 0.01),
        )

        if random.random() <= stick_chance:
            self._give_item(
                player,
                "minecraft:stick",
                1,
                leaf,
            )

        # Oak leaves can produce apples.
        if leaf_type == "minecraft:oak_leaves":
            apple_chance = min(
                1.0,
                0.005 + (fortune_level * 0.0025),
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

        leftovers = player.inventory.add_item(stack)

        if not leftovers:
            return

        for leftover in leftovers.values():
            source_block.dimension.drop_item(
                source_block.location,
                leftover,
            )

    def _play_effect(self, player, origin) -> None:
        if not self.config.get(
            "tree_capitator.effects.enabled",
            True,
        ):
            return

        bottom_particle = self.config.get(
            "tree_capitator.effects.bottom_particle",
            "ulkd_ess:essentials8",
        )

        top_particle = self.config.get(
            "tree_capitator.effects.top_particle",
            "ulkd_ess:essentials7",
        )

        start_y = float(
            self.config.get(
                "tree_capitator.effects.bottom_start_y",
                -0.9,
            )
        )

        bottom_end_y = float(
            self.config.get(
                "tree_capitator.effects.bottom_end_y",
                -0.1,
            )
        )

        top_start_y = float(
            self.config.get(
                "tree_capitator.effects.top_start_y",
                0.1,
            )
        )

        top_end_y = float(
            self.config.get(
                "tree_capitator.effects.top_end_y",
                0.9,
            )
        )

        step_y = float(
            self.config.get(
                "tree_capitator.effects.particle_step_y",
                0.2,
            )
        )

        x = origin.x + 0.5
        y = origin.y + 0.5
        z = origin.z + 0.5

        if bottom_particle:
            current_y = start_y

            while current_y <= bottom_end_y + 0.001:
                player.spawn_particle(
                    bottom_particle,
                    x,
                    y + current_y,
                    z,
                )

                current_y += step_y

        if top_particle:
            current_y = top_start_y

            while current_y <= top_end_y + 0.001:
                player.spawn_particle(
                    top_particle,
                    x,
                    y + current_y,
                    z,
                )

                current_y += step_y

        sound = self.config.get(
            "tree_capitator.effects.sound",
            "unlinked.essentials.log",
        )

        if not sound:
            return

        volume = float(
            self.config.get(
                "tree_capitator.effects.sound_volume",
                1.0,
            )
        )

        pitch = float(
            self.config.get(
                "tree_capitator.effects.sound_pitch",
                1.0,
            )
        )

        player.play_sound(
            origin.location,
            sound,
            volume,
            pitch,
        )

    @staticmethod
    def _get_type_id(type_object) -> str:
        if hasattr(type_object, "id"):
            return type_object.id

        return str(type_object)

    @staticmethod
    def _get_enchantment_level(item, enchantment) -> int:
        if item is None:
            return 0

        try:
            return item.item_meta.get_enchant_level(
                enchantment,
            )
        except (AttributeError, TypeError, ValueError):
            return 0

    @staticmethod
    def _has_enchantment(item, enchantment) -> bool:
        if item is None:
            return False

        try:
            return item.item_meta.has_enchant(
                enchantment,
            )
        except (AttributeError, TypeError, ValueError):
            return False