from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cards import PokemonCard, load_default_database
from deck import analyze_deck, load_deck_ids


def print_counter(title: str, counter) -> None:
    print(f"\n{title}:")
    if not counter:
        print("  none")
        return
    for key, count in sorted(counter.items(), key=lambda item: str(item[0])):
        print(f"  {key}: {count}")


def main() -> None:
    db = load_default_database()
    deck_ids = load_deck_ids(ROOT / "deck.csv")
    analysis = analyze_deck(deck_ids, db)

    print("Deck report")
    print(f"Total cards: {analysis.total_cards}")
    print(f"Unique cards: {analysis.unique_cards}")
    print(f"Pokemon: {analysis.pokemon_count}")
    print(f"Trainers: {analysis.trainer_count}")
    print(f"Energy: {analysis.energy_count}")
    print(f"Average Pokemon HP: {analysis.average_hp:.1f}")
    print(f"Average retreat: {analysis.average_retreat:.2f}")
    print(f"Max attack damage: {analysis.max_damage}")

    print_counter("Pokemon types", analysis.type_counts)
    print_counter("Energy types", analysis.energy_counts)
    print_counter("Weaknesses", analysis.weakness_counts)
    print_counter("Retreat costs", analysis.retreat_counts)

    print("\nEvolution lines:")
    if not analysis.evolution_lines:
        print("  none")
    for previous, evolutions in sorted(analysis.evolution_lines.items()):
        print(f"  {previous} -> {', '.join(sorted(evolutions))}")

    print("\nCards:")
    for card_id, count in sorted(analysis.card_counts.items()):
        card = db.get_card(card_id)
        tag = "Pokemon" if isinstance(card, PokemonCard) else card.kind
        print(f"  {count:>2}x {card.name} [{card_id}] ({tag})")


if __name__ == "__main__":
    main()
