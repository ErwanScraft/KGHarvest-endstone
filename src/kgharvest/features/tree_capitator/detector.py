from collections import deque


class TreeDetector:
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

    def __init__(self, config) -> None:
        self.config = config

    @staticmethod
    def type_id(type_object) -> str:
        if hasattr(type_object, "id"):
            return type_object.id

        return str(type_object)

    def is_axe(self, item) -> bool:
        if item is None:
            return False

        return self.type_id(item.type) in self.AXE_TYPES

    def is_log(self, block) -> bool:
        return self.type_id(block.type) in self.LOG_TYPES

    def is_leaf(self, block) -> bool:
        return self.type_id(block.type) in self.LEAF_TYPES

    def find_connected_logs(self, origin):
        max_logs = max(
            1,
            self.config.get_int(
                "tree_capitator.limits.logs",
                32,
            ),
        )

        if max_logs <= 1:
            return []

        dimension = origin.dimension

        origin_position = (
            origin.x,
            origin.y,
            origin.z,
        )

        queue = deque([origin_position])
        visited = {origin_position}
        connected = []

        while queue and len(connected) < max_logs - 1:
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

                if not self.is_log(block):
                    continue

                connected.append(block)
                queue.append(position)

                if len(connected) >= max_logs - 1:
                    break

        return connected

    def find_tree_leaves(self, logs, origin):
        max_leaves = self.config.get_int(
            "tree_capitator.limits.leaves",
            128,
        )

        if max_leaves <= 0 or not logs:
            return []

        dimension = origin.dimension

        queue = deque()
        visited = set()
        leaves = []

        for log in (origin, *logs):
            position = (
                log.x,
                log.y,
                log.z,
            )

            if position in visited:
                continue

            visited.add(position)
            queue.append(position)

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

                if self.is_leaf(block):
                    leaves.append(block)
                    queue.append(position)

                elif self.is_log(block):
                    queue.append(position)

                if len(leaves) >= max_leaves:
                    break

        return leaves