from __future__ import annotations

from pathlib import Path

from .models import Card, EnergyCard, PokemonCard, TrainerCard
from .parser import load_cards


class CardDatabase:
    def __init__(self, cards: dict[int, Card]):
        self.cards = dict(cards)

    @classmethod
    def from_csv(cls, csv_path: str | Path) -> "CardDatabase":
        return cls(load_cards(csv_path))

    def __len__(self) -> int:
        return len(self.cards)

    def get_card(self, card_id: int) -> Card:
        return self.cards[card_id]

    def all_cards(self) -> list[Card]:
        return list(self.cards.values())

    def pokemon(self) -> list[PokemonCard]:
        return [card for card in self.cards.values() if isinstance(card, PokemonCard)]

    def basic_pokemon(self) -> list[PokemonCard]:
        return [card for card in self.pokemon() if card.stage == "Basic Pokemon" or card.stage == "Basic Pokémon"]

    def stage1(self) -> list[PokemonCard]:
        return [card for card in self.pokemon() if "Stage 1" in card.stage]

    def stage2(self) -> list[PokemonCard]:
        return [card for card in self.pokemon() if "Stage 2" in card.stage]

    def trainers(self) -> list[TrainerCard]:
        return [card for card in self.cards.values() if isinstance(card, TrainerCard)]

    def energy_cards(self) -> list[EnergyCard]:
        return [card for card in self.cards.values() if isinstance(card, EnergyCard)]

    def by_type(self, type_name: str) -> list[Card]:
        return [card for card in self.cards.values() if card.card_type == type_name]

    def top_damage(self, limit: int = 10) -> list[PokemonCard]:
        return sorted(self.pokemon(), key=lambda card: card.max_damage, reverse=True)[:limit]


def load_default_database() -> CardDatabase:
    root = Path(__file__).resolve().parents[1]
    return CardDatabase.from_csv(root / "data" / "EN_Card_Data.csv")
