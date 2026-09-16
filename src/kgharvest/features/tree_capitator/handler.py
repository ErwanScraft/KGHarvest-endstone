from collections import deque

from endstone.event import BlockBreakEvent


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

    def __init__(self, plugin, config_manager, messages) -> None:
        self.plugin = plugin
        self.config_manager = config_manager
        self.messages = messages

        self.enabled = config_manager.get(
            "tree_capitator.enabled",
            True,
        )

        self.require_sneaking = config_manager.get(
            "tree_capitator.require_sneaking",
            True,
        )

        self.max_blocks = config_manager.get(
            "tree_capitator.max_blocks",
            32,
        )

    def handle(self, event: BlockBreakEvent) -> None:
        if not self.enabled:
            return

        player = event.player
        block = event.block

        has_permission = player.has_permission(
            "kgharvest.treecapitator"
        )

        self.plugin.logger.info(
            f"[DEBUG] BlockBreak player={player.name} "
            f"sneaking={player.is_sneaking} "
            f"permission={has_permission} "
            f"block={self._get_type_id(block.type)}"
        )

        if not has_permission:
            return

        if self.require_sneaking and not player.is_sneaking:
            return

        item = player.inventory.item_in_main_hand

        item_type = self._get_type_id(item.type) if item else None

        self.plugin.logger.info(
            f"[DEBUG] MainHand={item_type}"
        )

        if item is None:
            return

        if item_type not in self.AXE_TYPES:
            return

        block_type = self._get_type_id(block.type)

        if block_type not in self.LOG_TYPES:
            return

        tree_blocks = self._find_connected_logs(block)

        self.plugin.logger.info(
            f"[DEBUG] ConnectedLogs={len(tree_blocks)}"
        )

        if len(tree_blocks) <= 1:
            return

        for tree_block in tree_blocks:
            if self._is_same_block(tree_block, block):
                continue

            tree_block.set_type("minecraft:air")

    def _find_connected_logs(self, origin) -> list:
        found = []
        visited = set()

        queue = deque(
            [
                (
                    origin.x,
                    origin.y,
                    origin.z,
                )
            ]
        )

        while queue and len(found) < self.max_blocks:
            x, y, z = queue.popleft()

            position = (x, y, z)

            if position in visited:
                continue

            visited.add(position)

            block = origin.dimension.get_block_at(
                x,
                y,
                z,
            )

            block_type = self._get_type_id(block.type)

            if block_type not in self.LOG_TYPES:
                continue

            found.append(block)

            for offset_x, offset_y, offset_z in self.DIRECTIONS:
                queue.append(
                    (
                        x + offset_x,
                        y + offset_y,
                        z + offset_z,
                    )
                )

        return found

    @staticmethod
    def _get_type_id(type_object) -> str:
        return str(type_object)

    @staticmethod
    def _is_same_block(first, second) -> bool:
        return (
            first.x == second.x
            and first.y == second.y
            and first.z == second.z
        )