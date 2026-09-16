import random


class TreeCapitatorEffects:
    def __init__(self, config) -> None:
        self.config = config

    def play_log_effect(
        self,
        player,
        block,
        sound_counter: int,
    ) -> int:
        if not self.config.get_bool(
            "tree_capitator.effects.enabled",
            True,
        ):
            return sound_counter

        self._spawn_log_particles(
            player,
            block,
        )

        sound_counter += 1

        interval = max(
            1,
            self.config.get_int(
                "tree_capitator.effects.sound.interval",
                2,
            ),
        )

        if sound_counter % interval == 0:
            self._play_log_sound(
                player,
                block,
            )

        return sound_counter

    def play_leaf_effect(
        self,
        player,
        block,
    ) -> None:
        if not self.config.get_bool(
            "tree_capitator.effects.enabled",
            True,
        ):
            return

        particle = self.config.get(
            "tree_capitator.effects.particles.leaf",
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

    def _spawn_log_particles(
        self,
        player,
        block,
    ) -> None:
        x = block.x + 0.5
        y = block.y + 0.5
        z = block.z + 0.5

        particles = "tree_capitator.effects.particles"

        step = self.config.get_float(
            f"{particles}.step_y",
            0.2,
        )

        if step <= 0:
            step = 0.2

        bottom_particle = self.config.get(
            f"{particles}.log_bottom",
            "kgserver:break1",
        )

        top_particle = self.config.get(
            f"{particles}.log_top",
            "kgserver:break2",
        )

        if bottom_particle:
            self._spawn_column(
                player,
                bottom_particle,
                x,
                y,
                z,
                self.config.get_float(
                    f"{particles}.bottom.start_y",
                    -0.9,
                ),
                self.config.get_float(
                    f"{particles}.bottom.end_y",
                    -0.1,
                ),
                step,
            )

        if top_particle:
            self._spawn_column(
                player,
                top_particle,
                x,
                y,
                z,
                self.config.get_float(
                    f"{particles}.top.start_y",
                    0.1,
                ),
                self.config.get_float(
                    f"{particles}.top.end_y",
                    0.9,
                ),
                step,
            )

    @staticmethod
    def _spawn_column(
        player,
        particle,
        x,
        y,
        z,
        start_y,
        end_y,
        step,
    ) -> None:
        current_y = start_y

        while current_y <= end_y + 0.001:
            player.spawn_particle(
                particle,
                x,
                y + current_y,
                z,
            )

            current_y += step

    def _play_log_sound(
        self,
        player,
        block,
    ) -> None:
        sound = self.config.get(
            "tree_capitator.effects.sound.name",
            "kgserver.break.log",
        )

        if not sound:
            return

        volume = self.config.get_float(
            "tree_capitator.effects.sound.volume",
            0.75,
        )

        pitch = self.config.get_float(
            "tree_capitator.effects.sound.pitch",
            1.0,
        )

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