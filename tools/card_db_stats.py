from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cards import CardDatabase, PokemonCard, load_default_database


def load_deck_ids(path: Path) -> list[int]:
    return [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]


def print_deck_summary(db: CardDatabase) -> None:
    deck_ids = load_deck_ids(ROOT / "deck.csv")
    counts = Counter(deck_ids)
    print("\nCurrent deck:")
    for card_id, count in sorted(counts.items()):
        card = db.get_card(card_id)
        print(f"{count:>2}x {card.name} [{card_id}]")


def main() -> None:
    db = load_default_database()
    print(f"Total cards: {len(db)}")
    print(f"Pokemon: {len(db.pokemon())}")
    print(f"Basic Pokemon: {len(db.basic_pokemon())}")
    print(f"Stage 1 Pokemon: {len(db.stage1())}")
    print(f"Stage 2 Pokemon: {len(db.stage2())}")
    print(f"Trainers: {len(db.trainers())}")
    print(f"Energy: {len(db.energy_cards())}")

    print("\nTop damage:")
    for card in db.top_damage(10):
        assert isinstance(card, PokemonCard)
        print(f"{card.max_damage:>3}  {card.name} [{card.card_id}]")

    print_deck_summary(db)


if __name__ == "__main__":
    main()
