from collections import deque
import random

from endstone.event import BlockBreakEvent
from endstone.inventory import ItemStack


class TreeCapitatorHandler:
    PERMISSION = "kgharvest.treecapitator"

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

    DIRECTIONS = tuple(
        (x, y, z)
        for x in (-1, 0, 1)
        for y in (-1, 0, 1)
        for z in (-1, 0, 1)
        if (x, y, z) != (0, 0, 0)
    )

    def __init__(self, plugin, config, messages) -> None:
        self.plugin = plugin
        self.config = config
        self.messages = messages

        # Player UUIDs currently running a Tree Capitator session.
        self.active_players = set()

    def handle(self, event: BlockBreakEvent) -> None:
        player = event.player
        block = event.block

        if not self.config.get(
            "tree_capitator.enabled",
            True,
        ):
            return

        if not player.has_permission(self.PERMISSION):
            return

        if (
            self.config.get(
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

        if item is None:
            return

        if self._get_type_id(item.type) not in self.AXE_TYPES:
            return

        block_type = self._get_type_id(block.type)

        if block_type not in self.LOG_TYPES:
            return

        additional_logs = self._find_connected_logs(block)

        if not additional_logs:
            return

        leaves = self._find_tree_leaves(
            additional_logs,
            block,
        )

        self.active_players.add(player_id)

        state = {
            "player": player,
            "logs": list(additional_logs),
            "leaves": list(leaves),
            "log_index": 0,
            "leaf_index": 0,
            "sound_counter": 0,
        }

        self.plugin.logger.debug(
            f"TreeCapitator player={player.name} "
            f"logs={len(additional_logs) + 1} "
            f"leaves={len(leaves)}"
        )

        self._start_harvest(state)

    def update_indicator(self, player) -> None:
        """
        Shows the Tree Capitator status while the player is
        sneaking and has the required permission.
        """

        if not self.config.get(
            "tree_capitator.indicator.enabled",
            True,
        ):
            return

        if not player.has_permission(self.PERMISSION):
            return

        if not player.is_sneaking:
            return

        message = self.messages.get(
            "tree_capitator.active",
            "<green>● Tree Capitator Active</green>",
        )

        player.send_tip(message)

    def _start_harvest(self, state) -> None:
        delay = max(
            1,
            int(
                self.config.get(
                    "tree_capitator.animation.delay",
                    1,
                )
            ),
        )

        self.plugin.server.scheduler.run_task(
            self.plugin,
            lambda: self._animation_tick(state),
            delay=delay,
            period=delay,
        )

    def _animation_tick(self, state) -> None:
        player = state["player"]
        player_id = str(player.unique_id)

        if player_id not in self.active_players:
            return

        # Stop the animation if the player no longer holds an axe.
        if not self._tool_is_valid(player):
            self._finish_harvest(state)
            return

        logs = state["logs"]

        logs_per_tick = max(
            1,
            int(
                self.config.get(
                    "tree_capitator.animation.logs_per_tick",
                    1,
                )
            ),
        )

        processed = 0

        while (
            state["log_index"] < len(logs)
            and processed < logs_per_tick
        ):
            tree_block = logs[state["log_index"]]

            if not self._process_log(
                player,
                tree_block,
                state,
            ):
                self._finish_harvest(state)
                return

            state["log_index"] += 1
            processed += 1

        # Continue the next tick until every log is processed.
        if state["log_index"] < len(logs):
            return

        leaves = state["leaves"]

        leaves_per_tick = max(
            1,
            int(
                self.config.get(
                    "tree_capitator.animation.leaves_per_tick",
                    4,
                )
            ),
        )

        processed = 0

        while (
            state["leaf_index"] < len(leaves)
            and processed < leaves_per_tick
        ):
            self._process_leaf(
                player,
                leaves[state["leaf_index"]],
            )

            state["leaf_index"] += 1
            processed += 1

        if state["leaf_index"] >= len(leaves):
            self._finish_harvest(state)

    def _process_log(
        self,
        player,
        tree_block,
        state,
    ) -> bool:
        log_type = self._get_type_id(tree_block.type)

        # The block may already have been removed by another action.
        if log_type not in self.LOG_TYPES:
            return True

        self._play_break_effect(
            player,
            tree_block,
            state,
        )

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

        # Every additional log consumes one durability attempt.
        return self._damage_tool(player)

    def _process_leaf(
        self,
        player,
        leaf,
    ) -> None:
        leaf_type = self._get_type_id(leaf.type)

        if leaf_type not in self.LEAF_TYPES:
            return

        self._play_leaf_effect(
            player,
            leaf,
        )

        leaf.set_type(
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
                leaf,
            )
            return

        self._process_leaf_drops(
            player,
            leaf,
            leaf_type,
            fortune_level,
        )

    def _damage_tool(self, player) -> bool:
        """
        Applies one durability attempt to the currently held axe.

        Returns False when the axe breaks.
        """

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

        # Unbreaking gives the tool a chance to avoid durability loss.
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
            # Axe has broken.
            player.inventory.item_in_main_hand = None
            return False

        meta.damage = new_damage
        item.set_item_meta(meta)

        return True

    def _tool_is_valid(self, player) -> bool:
        item = player.inventory.item_in_main_hand

        if item is None:
            return False

        return (
            self._get_type_id(item.type)
            in self.AXE_TYPES
        )

    def _play_break_effect(
        self,
        player,
        block,
        state,
    ) -> None:
        if not self.config.get(
            "tree_capitator.effects.enabled",
            True,
        ):
            return

        x = block.x + 0.5
        y = block.y + 0.5
        z = block.z + 0.5

        bottom_particle = self.config.get(
            "tree_capitator.effects.bottom_particle",
            "kgserver:break1",
        )

        top_particle = self.config.get(
            "tree_capitator.effects.top_particle",
            "kgserver:break2",
        )

        step = float(
            self.config.get(
                "tree_capitator.effects.particle_step_y",
                0.2,
            )
        )

        if step <= 0:
            step = 0.2

        # Lower particle column.
        if bottom_particle:
            current_y = float(
                self.config.get(
                    "tree_capitator.effects.bottom_start_y",
                    -0.9,
                )
            )

            end_y = float(
                self.config.get(
                    "tree_capitator.effects.bottom_end_y",
                    -0.1,
                )
            )

            while current_y <= end_y + 0.001:
                player.spawn_particle(
                    bottom_particle,
                    x,
                    y + current_y,
                    z,
                )

                current_y += step

        # Upper particle column.
        if top_particle:
            current_y = float(
                self.config.get(
                    "tree_capitator.effects.top_start_y",
                    0.1,
                )
            )

            end_y = float(
                self.config.get(
                    "tree_capitator.effects.top_end_y",
                    0.9,
                )
            )

            while current_y <= end_y + 0.001:
                player.spawn_particle(
                    top_particle,
                    x,
                    y + current_y,
                    z,
                )

                current_y += step

        # Don't play the sound for every single block.
        state["sound_counter"] += 1

        sound_interval = max(
            1,
            int(
                self.config.get(
                    "tree_capitator.effects.sound_interval",
                    2,
                )
            ),
        )

        if (
            state["sound_counter"]
            % sound_interval
            != 0
        ):
            return

        sound = self.config.get(
            "tree_capitator.effects.sound",
            "kgserver.break.log",
        )

        if not sound:
            return

        volume = float(
            self.config.get(
                "tree_capitator.effects.sound_volume",
                0.75,
            )
        )

        pitch = float(
            self.config.get(
                "tree_capitator.effects.sound_pitch",
                1.0,
            )
        )

        # Small variation prevents repetitive audio.
        pitch += random.uniform(
            -0.04,
            0.04,
        )

        player.play_sound(
            block.location,
            sound,
            volume,
            pitch,
        )

    def _play_leaf_effect(
        self,
        player,
        block,
    ) -> None:
        if not self.config.get(
            "tree_capitator.effects.enabled",
            True,
        ):
            return

        particle = self.config.get(
            "tree_capitator.effects.leaf_particle",
            "kgserver:break1",
        )

        if not particle:
            return

        player.spawn_particle(
            particle,
            block.x + 0.5,
            block.y + 0.5,
            block.z + 0.5,
        )

    def _find_connected_logs(
        self,
        origin,
    ):
        max_blocks = int(
            self.config.get(
                "tree_capitator.max_blocks",
                32,
            )
        )

        if max_blocks <= 1:
            return []

        dimension = origin.dimension

        origin_position = (
            origin.x,
            origin.y,
            origin.z,
        )

        queue = deque(
            [origin_position]
        )

        visited = {
            origin_position
        }

        connected = []

        while (
            queue
            and len(connected)
            < max_blocks - 1
        ):
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

                if (
                    self._get_type_id(block.type)
                    not in self.LOG_TYPES
                ):
                    continue

                connected.append(block)
                queue.append(position)

                if (
                    len(connected)
                    >= max_blocks - 1
                ):
                    break

        return connected

    def _find_tree_leaves(
        self,
        logs,
        origin,
    ):
        max_leaves = int(
            self.config.get(
                "tree_capitator.max_leaves",
                128,
            )
        )

        if max_leaves <= 0 or not logs:
            return []

        dimension = origin.dimension

        queue = deque()
        visited = set()
        leaves = []

        log_blocks = [
            origin,
            *logs,
        ]

        for log in log_blocks:
            position = (
                log.x,
                log.y,
                log.z,
            )

            queue.append(position)
            visited.add(position)

        while (
            queue
            and len(leaves) < max_leaves
        ):
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

                block_type = self._get_type_id(
                    block.type
                )

                if block_type in self.LEAF_TYPES:
                    leaves.append(block)
                    queue.append(position)

                elif block_type in self.LOG_TYPES:
                    queue.append(position)

                if len(leaves) >= max_leaves:
                    break

        return leaves

    def _process_leaf_drops(
        self,
        player,
        leaf,
        leaf_type,
        fortune_level,
    ) -> None:
        sapling = self.LEAF_TO_SAPLING.get(
            leaf_type
        )

        if sapling is None:
            return

        sapling_chance = min(
            1.0,
            0.05
            + fortune_level * 0.025,
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
            0.02
            + fortune_level * 0.01,
        )

        if random.random() <= stick_chance:
            self._give_item(
                player,
                "minecraft:stick",
                1,
                leaf,
            )

        if (
            leaf_type
            == "minecraft:oak_leaves"
        ):
            apple_chance = min(
                1.0,
                0.005
                + fortune_level * 0.0025,
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
            stack
        )

        if not leftovers:
            return

        for leftover in leftovers.values():
            source_block.dimension.drop_item(
                source_block.location,
                leftover,
            )

    def _finish_harvest(self, state) -> None:
        player_id = str(
            state["player"].unique_id
        )

        self.active_players.discard(
            player_id
        )

    @staticmethod
    def _get_type_id(type_object) -> str:
        if hasattr(type_object, "id"):
            return type_object.id

        return str(type_object)

    @staticmethod
    def _get_enchantment_level(
        item,
        enchantment,
    ) -> int:
        if item is None:
            return 0

        try:
            return item.item_meta.get_enchant_level(
                enchantment
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
                enchantment
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return False