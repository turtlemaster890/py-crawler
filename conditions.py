from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from enemy import Enemy
    from combatHandler import CombatHandler


class Condition:
    def __init__(
        self,
        name: str,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
    ) -> None:
        self.name: str = name
        self.duration: int = duration
        self.affected: Player | Enemy = affected
        self.combat: CombatHandler = handler

    def changeDuration(self, amount: int) -> None:
        self.duration += amount
        if self.duration <= 0:
            self.affected.conditions.remove(self)

    def turnStart(self) -> None:
        self.changeDuration(-1)

    def turnEnd(self) -> None:
        pass

    def takeDamage(
        self, amount, attacker=None, defender=None, damage_type=None
    ) -> None:
        pass

    def die(self) -> None:
        pass

    def dealDamage(
        self, amount, attacker=None, defender=None, damage_type=None
    ) -> None:
        pass

    def enemyDeath(self, enemy) -> None:
        pass

    def inflictCondition(self, condition, target) -> None:
        pass


class Slimed(Condition):
    def __init__(
        self,
        duration: int,
        affected: Player | Enemy,
        handler: CombatHandler,
        name: str = "Slimed",
    ) -> None:
        super().__init__(name, duration, affected, handler)

    def turnStart(self) -> None:
        super().turnStart()
        self.affected.speed -= 5
