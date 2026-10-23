from actions import CombatActionEntry, PlayerAction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from combatHandler import CombatHandler


class PlayerClass:
    combat_actions: list[CombatActionEntry] = []
    player_actions: list[tuple[str, PlayerAction]] = []


class Tank(PlayerClass):
    @staticmethod
    def taunt(player: Player, handler: CombatHandler):
        for enemy in handler.enemies:
            for ag in enemy.aggro:
                if ag.player is player:
                    ag.value += 35

    combat_actions = [CombatActionEntry("Taunt", taunt, "Taunt all enemies", 2)]


classes = {"tank": Tank}


def classFromStr(className: str) -> type[PlayerClass]:
    return classes.get(className, PlayerClass)
