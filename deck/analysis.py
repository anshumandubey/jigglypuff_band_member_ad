from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from cards import CardDatabase, EnergyCard, PokemonCard, TrainerCard


@dataclass(frozen=True)
class DeckAnalysis:
    total_cards: int
    unique_cards: int
    pokemon_count: int
    trainer_count: int
    energy_count: int
    type_counts: Counter[str]
    energy_counts: Counter[str]
    weakness_counts: Counter[str]
    retreat_counts: Counter[int]
    hp_values: list[int]
    damage_values: list[int]
    evolution_lines: dict[str, list[str]]
    card_counts: Counter[int]

    @property
    def average_hp(self) -> float:
        return sum(self.hp_values) / len(self.hp_values) if self.hp_values else 0.0

    @property
    def average_retreat(self) -> float:
        total = sum(cost * count for cost, count in self.retreat_counts.items())
        count = sum(self.retreat_counts.values())
        return total / count if count else 0.0

    @property
    def max_damage(self) -> int:
        return max(self.damage_values, default=0)


def analyze_deck(deck_ids: list[int], db: CardDatabase) -> DeckAnalysis:
    counts = Counter(deck_ids)
    pokemon_count = 0
    trainer_count = 0
    energy_count = 0
    type_counts: Counter[str] = Counter()
    energy_counts: Counter[str] = Counter()
    weakness_counts: Counter[str] = Counter()
    retreat_counts: Counter[int] = Counter()
    hp_values: list[int] = []
    damage_values: list[int] = []
    evolution_lines: dict[str, list[str]] = defaultdict(list)

    for card_id, count in counts.items():
        card = db.get_card(card_id)
        if isinstance(card, PokemonCard):
            pokemon_count += count
            if card.card_type:
                type_counts[card.card_type] += count
            if card.weakness:
                weakness_counts[card.weakness] += count
            if card.retreat is not None:
                retreat_counts[card.retreat] += count
            if card.hp is not None:
                hp_values.extend([card.hp] * count)
            if card.max_damage:
                damage_values.extend([card.max_damage] * count)
            if card.previous_stage:
                evolution_lines[card.previous_stage].append(card.name)
        elif isinstance(card, TrainerCard):
            trainer_count += count
        elif isinstance(card, EnergyCard):
            energy_count += count
            energy_counts[card.card_type or card.energy_type] += count

    return DeckAnalysis(
        total_cards=len(deck_ids),
        unique_cards=len(counts),
        pokemon_count=pokemon_count,
        trainer_count=trainer_count,
        energy_count=energy_count,
        type_counts=type_counts,
        energy_counts=energy_counts,
        weakness_counts=weakness_counts,
        retreat_counts=retreat_counts,
        hp_values=hp_values,
        damage_values=damage_values,
        evolution_lines=dict(evolution_lines),
        card_counts=counts,
    )
