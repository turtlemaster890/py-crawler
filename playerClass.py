from actions import CombatActionEntry, PlayerAction
from typing import TYPE_CHECKING

import conditions
from terminalDisplay import say

if TYPE_CHECKING:
    from player import Player
    from enemy import Enemy
    from combatHandler import CombatHandler


def pick_enemy(handler: CombatHandler) -> Player | Enemy:
    return handler.select_character(lambda c: c in handler.enemies)[0]


def weapon_damage(player: Player) -> int:
    return player.inventory.weapon.damage if player.inventory.weapon else 1


class PlayerClass:
    combat_actions: list[CombatActionEntry] = []
    player_actions: list[tuple[str, PlayerAction]] = []


class Tank(PlayerClass):
    @staticmethod
    def taunt(player: Player, handler: CombatHandler) -> bool:
        for enemy in handler.enemies:
            for ag in enemy.aggro:
                if ag.player is player:
                    ag.value += 35
        say(
            f"{player.name} yells out an obscenity. All the enemies seem very angered at them."
        )
        return True

    combat_actions = [CombatActionEntry("Taunt", taunt, "Taunt all enemies", 2)]


class Warrior(PlayerClass):
    @staticmethod
    def shield_bash(player: Player, handler: CombatHandler) -> bool:
        target = pick_enemy(handler)
        dmg = player.relicDamage(max(1, weapon_damage(player) // 2), target)
        target.takeDamage(handler, dmg, player)
        if target.health > 0:
            conditions.inflict({"type": "stunned", "duration": 1}, target, handler)
            say(f"{player.name} bashes {target.name}, stunning them!")
        return True

    @staticmethod
    def guard(player: Player, handler: CombatHandler) -> bool:
        player.applyCondition(conditions.Shield(3, player, handler, absorb=15), handler)
        say(f"{player.name} raises their shield.")
        return True

    combat_actions = [
        CombatActionEntry(
            "Shield Bash", shield_bash, "Half weapon damage + 1 turn stun", 8
        ),
        CombatActionEntry("Guard", guard, "Absorb 15 damage for up to 3 turns", 10),
    ]


class Mage(PlayerClass):
    @staticmethod
    def frost_nova(player: Player, handler: CombatHandler) -> bool:
        for e in handler.enemies[:]:
            e.takeDamage(handler, player.relicDamage(4, e, "magic"), player)
            if e.health > 0:
                conditions.inflict({"type": "chilled", "duration": 2}, e, handler)
        say(
            f"{player.name} unleashes a blast of air. The surroundings suddenly feel very cold."
        )
        return True

    @staticmethod
    def arcane_barrier(player: Player, handler: CombatHandler):
        ally = handler.select_character(
            lambda c: c in handler.players and c is not player
        )[0]
        ally.applyCondition(conditions.Shield(100, ally, handler, absorb=12), handler)
        say(
            f"{player.name} casts a spell on {ally.name}. They suddenly feel protected."
        )
        return True

    combat_actions = [
        CombatActionEntry("Frost Nova", frost_nova, "Damage and slow ALL enemies", 12),
        CombatActionEntry(
            "Arcane Barrier", arcane_barrier, "Shield an ally for 12 damage", 10
        ),
    ]


class Rogue(PlayerClass):
    @staticmethod
    def backstab(player: Player, handler: CombatHandler) -> bool:
        target = pick_enemy(handler)
        dmg = weapon_damage(player) * (3 if target.conditions else 2)
        target.takeDamage(handler, player.relicDamage(dmg, target), player)
        if target.health > 0:
            conditions.inflict({"type": "bleeding", "duration": 3}, target, handler)
        say(f"{player.name} sneaks behind {target.name} and stabs them in the back.")
        return True

    @staticmethod
    def venom_strike(player: Player, handler: CombatHandler) -> bool:
        target = pick_enemy(handler)
        target.takeDamage(
            handler, player.relicDamage(weapon_damage(player), target), player
        )
        if target.health > 0:
            conditions.inflict({"type": "poisoned", "duration": 4}, target, handler)
            say(f"{target.name} is poisoned!")
        return True

    combat_actions = [
        CombatActionEntry(
            "Backstab",
            backstab,
            "2x damage (3x if target has a condition) and bleed",
            8,
        ),
        CombatActionEntry("Venom Strike", venom_strike, "Weapon hit and poison", 10),
    ]


classes: dict[str, type[PlayerClass]] = {
    "tank": Tank,
    "warrior": Warrior,
    "mage": Mage,
    "rogue": Rogue,
}


def classFromStr(className: str) -> type[PlayerClass]:
    return classes.get(className, PlayerClass)
