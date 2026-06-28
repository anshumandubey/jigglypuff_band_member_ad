from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from .models import Card, EnergyCard, Move, PokemonCard, TrainerCard

STAGE_FIELD = "Stage (Pokemon)/Type (Energy and Trainer)"
RAW_STAGE_FIELD = "Stage (Pokémon)/Type (Energy and Trainer)"


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text.lower() == "n/a":
        return None
    return text


def parse_int(value: str | None) -> int | None:
    text = clean(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_cost(value: str | None) -> tuple[str, ...]:
    text = clean(value)
    if text is None:
        return ()
    symbols = re.findall(r"\{[^}]+\}|●", text)
    return tuple(symbols)


def parse_damage(value: str | None) -> int | None:
    text = clean(value)
    if text is None:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def _stage(row: dict[str, str]) -> str:
    return clean(row.get(RAW_STAGE_FIELD) or row.get(STAGE_FIELD)) or ""


def _is_pokemon_stage(kind: str) -> bool:
    return kind in {
        "Basic Pokemon",
        "Basic Pokémon",
        "Stage 1 Pokemon",
        "Stage 1 Pokémon",
        "Stage 2 Pokemon",
        "Stage 2 Pokémon",
    }


def _move_from_row(row: dict[str, str]) -> Move | None:
    name = clean(row.get("Move Name"))
    damage_text = clean(row.get("Damage"))
    effect = clean(row.get("Effect Explanation"))
    cost = parse_cost(row.get("Cost"))
    if not name and not damage_text and not effect and not cost:
        return None
    return Move(
        name=name or "",
        cost=cost,
        damage_text=damage_text,
        damage=parse_damage(damage_text),
        effect=effect,
    )


def load_cards(csv_path: str | Path) -> dict[int, Card]:
    rows_by_id: dict[int, list[dict[str, str]]] = defaultdict(list)
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            card_id = parse_int(row.get("Card ID"))
            if card_id is not None:
                rows_by_id[card_id].append(row)

    cards: dict[int, Card] = {}
    for card_id, rows in rows_by_id.items():
        first = rows[0]
        kind = _stage(first)
        base = {
            "card_id": card_id,
            "name": clean(first.get("Card Name")) or "",
            "expansion": clean(first.get("Expansion")) or "",
            "collection_no": clean(first.get("Collection No.")) or "",
            "kind": kind,
            "rule": clean(first.get("Rule")),
            "category": clean(first.get("Category")),
            "card_type": clean(first.get("Type")),
            "effect": clean(first.get("Effect Explanation")),
        }

        if _is_pokemon_stage(kind):
            moves = tuple(move for row in rows if (move := _move_from_row(row)))
            cards[card_id] = PokemonCard(
                **base,
                stage=kind,
                previous_stage=clean(first.get("Previous stage")),
                hp=parse_int(first.get("HP")),
                weakness=clean(first.get("Weakness")),
                resistance=clean(first.get("Resistance (Type)")),
                retreat=parse_int(first.get("Retreat")),
                moves=moves,
            )
        elif "Energy" in kind:
            cards[card_id] = EnergyCard(
                **base,
                energy_type=kind,
            )
        elif kind in {"Item", "Pokemon Tool", "Pokémon Tool", "Supporter", "Stadium"}:
            cards[card_id] = TrainerCard(
                **base,
                trainer_type=kind,
            )
        else:
            cards[card_id] = Card(**base)

    return cards
