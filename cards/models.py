from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Move:
    name: str
    cost: tuple[str, ...] = ()
    damage_text: str | None = None
    damage: int | None = None
    effect: str | None = None


@dataclass(frozen=True)
class Card:
    card_id: int
    name: str
    expansion: str
    collection_no: str
    kind: str
    rule: str | None = None
    category: str | None = None
    card_type: str | None = None
    effect: str | None = None

    @property
    def is_pokemon(self) -> bool:
        return False

    @property
    def is_trainer(self) -> bool:
        return False

    @property
    def is_energy(self) -> bool:
        return False


@dataclass(frozen=True)
class PokemonCard(Card):
    stage: str = ""
    previous_stage: str | None = None
    hp: int | None = None
    weakness: str | None = None
    resistance: str | None = None
    retreat: int | None = None
    moves: tuple[Move, ...] = field(default_factory=tuple)

    @property
    def is_pokemon(self) -> bool:
        return True

    @property
    def max_damage(self) -> int:
        damages = [move.damage for move in self.moves if move.damage is not None]
        return max(damages, default=0)


@dataclass(frozen=True)
class TrainerCard(Card):
    trainer_type: str = ""

    @property
    def is_trainer(self) -> bool:
        return True


@dataclass(frozen=True)
class EnergyCard(Card):
    energy_type: str = ""

    @property
    def is_energy(self) -> bool:
        return True
