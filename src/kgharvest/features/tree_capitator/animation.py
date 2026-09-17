class TreeCapitatorAnimation:
    def __init__(
        self,
        plugin,
        config,
        process_log,
        process_leaf,
        is_tool_valid,
        finish,
    ) -> None:
        self.plugin = plugin
        self.config = config
        self.process_log = process_log
        self.process_leaf = process_leaf
        self.is_tool_valid = is_tool_valid
        self.finish = finish
        self.tasks = {}

    def start(self, state) -> None:
        delay = max(
            1,
            self.config.get_int(
                "tree_capitator.animation.delay",
                1,
            ),
        )
    
        player_id = str(
            state["player"].unique_id
        )
    
        task = self.plugin.server.scheduler.run_task(
            self.plugin,
            lambda: self.tick(state),
            delay=delay,
            period=delay,
        )
    
        self.tasks[player_id] = task
    
    def _cancel_task(self, state) -> None:
        player_id = str(
            state["player"].unique_id
        )
    
        task = self.tasks.pop(
            player_id,
            None,
        )
    
        if task is None:
            return
    
        try:
            task.cancel()
        except (
            AttributeError,
            RuntimeError,
        ):
            pass

    def tick(self, state) -> None:
        if not state["active"]:
            self._cancel_task(state)
            return
    
        player = state["player"]
        player_id = str(player.unique_id)
    
        if player_id not in state["active_players"]:
            state["active"] = False
            self._cancel_task(state)
            return

        if not self.is_tool_valid(player):
            self.finish(state)
            return

        if not self.config.get_bool(
            "tree_capitator.animation.enabled",
            True,
        ):
            self._process_all(state)
            return

        if not self._process_logs(state):
            return

        if not self._process_leaves(state):
            return

        self.finish(state)

    def _process_logs(self, state) -> bool:
        logs = state["logs"]

        amount = max(
            1,
            self.config.get_int(
                "tree_capitator.animation.logs_per_tick",
                1,
            ),
        )

        processed = 0

        while (
            state["log_index"] < len(logs)
            and processed < amount
        ):
            block = logs[state["log_index"]]

            if not self.process_log(
                state,
                block,
            ):
                self.finish(state)
                return False

            state["log_index"] += 1
            processed += 1

        return state["log_index"] >= len(logs)

    def _process_leaves(self, state) -> bool:
        leaves = state["leaves"]

        amount = max(
            1,
            self.config.get_int(
                "tree_capitator.animation.leaves_per_tick",
                4,
            ),
        )

        processed = 0

        while (
            state["leaf_index"] < len(leaves)
            and processed < amount
        ):
            block = leaves[state["leaf_index"]]

            self.process_leaf(
                state,
                block,
            )

            state["leaf_index"] += 1
            processed += 1

        return state["leaf_index"] >= len(leaves)

    def _process_all(self, state) -> None:
        while state["log_index"] < len(state["logs"]):
            block = state["logs"][state["log_index"]]

            if not self.process_log(
                state,
                block,
            ):
                self.finish(state)
                return

            state["log_index"] += 1

        while state["leaf_index"] < len(state["leaves"]):
            block = state["leaves"][state["leaf_index"]]

            self.process_leaf(
                state,
                block,
            )

            state["leaf_index"] += 1

        self.finish(state)
    
    def cancel(self, state) -> None:
        self._cancel_task(state)