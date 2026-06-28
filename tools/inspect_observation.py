from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cards import CardDatabase, load_default_database


AREA_NAMES = {
    1: "deck",
    2: "hand",
    3: "discard",
    4: "active",
    5: "bench",
    6: "prize",
    7: "stadium",
    8: "energy",
    9: "tool",
    10: "pre_evolution",
    11: "player",
    12: "looking",
}

OPTION_TYPES = {
    0: "number",
    1: "yes",
    2: "no",
    3: "card",
    4: "tool_card",
    5: "energy_card",
    6: "energy",
    7: "play",
    8: "attach",
    9: "evolve",
    10: "ability",
    11: "discard",
    12: "retreat",
    13: "attack",
    14: "end",
    15: "skill",
    16: "special_condition",
}


def card_name(db: CardDatabase, card_id: int | None) -> str:
    if card_id is None:
        return "unknown"
    try:
        return db.get_card(card_id).name
    except KeyError:
        return f"unknown card {card_id}"


def format_card(card: dict[str, Any] | None, db: CardDatabase) -> str:
    if not card:
        return "empty"
    name = card_name(db, card.get("id"))
    hp = card.get("hp")
    max_hp = card.get("maxHp")
    hp_text = f" HP {hp}/{max_hp}" if hp is not None and max_hp is not None else ""
    energies = len(card.get("energyCards") or card.get("energies") or [])
    tools = len(card.get("tools") or [])
    extras = []
    if energies:
        extras.append(f"{energies} energy")
    if tools:
        extras.append(f"{tools} tool")
    extra_text = f" ({', '.join(extras)})" if extras else ""
    return f"{name}{hp_text}{extra_text}"


def format_hand(cards: list[dict[str, Any]], db: CardDatabase) -> str:
    if not cards:
        return "empty"
    return ", ".join(card_name(db, card.get("id")) for card in cards if card)


def format_option(option: dict[str, Any], db: CardDatabase) -> str:
    option_type = OPTION_TYPES.get(option.get("type"), f"type {option.get('type')}")
    if "id" in option:
        return f"{option_type}: {card_name(db, option.get('id'))}"
    if "attackId" in option:
        return f"{option_type}: attack {option.get('attackId')}"
    if "area" in option:
        area = AREA_NAMES.get(option.get("area"), f"area {option.get('area')}")
        target = f"{option_type}: {area}[{option.get('index')}] player {option.get('playerIndex')}"
        if "inPlayArea" in option:
            in_play_area = AREA_NAMES.get(option.get("inPlayArea"), f"area {option.get('inPlayArea')}")
            target += f" -> {in_play_area}[{option.get('inPlayIndex')}]"
        return target
    if "index" in option:
        return f"{option_type}: index {option.get('index')}"
    if "number" in option:
        return f"{option_type}: {option.get('number')}"
    return option_type


def inspect_observation(obs: dict[str, Any], db: CardDatabase | None = None, max_options: int = 20) -> str:
    db = db or load_default_database()
    current = obs.get("current", {})
    select = obs.get("select", {})
    players = current.get("players", [])
    your_index = current.get("yourIndex", 0)

    lines = [
        f"Turn: {current.get('turn')} | Player: {your_index} | Result: {current.get('result')}",
        f"Context: {select.get('context')} | Options: {len(select.get('option', []))}",
    ]

    for player_index, player in enumerate(players):
        label = "You" if player_index == your_index else "Opponent"
        hand = player.get("hand") or []
        active = player.get("active") or []
        bench = player.get("bench") or []
        prize = player.get("prize") or []
        discard = player.get("discard") or []
        lines.append(f"\n{label} P{player_index}")
        lines.append(f"  Active: {', '.join(format_card(card, db) for card in active) or 'empty'}")
        lines.append(f"  Bench: {', '.join(format_card(card, db) for card in bench) or 'empty'}")
        lines.append(f"  Hand: {player.get('handCount', len(hand))} cards")
        if player_index == your_index:
            lines.append(f"  Hand names: {format_hand(hand, db)}")
        lines.append(f"  Deck: {player.get('deckCount')} | Prize: {len(prize)} | Discard: {len(discard)}")

    options = select.get("option", [])
    lines.append("\nLegal actions:")
    for index, option in enumerate(options[:max_options]):
        lines.append(f"  [{index}] {format_option(option, db)}")
    if len(options) > max_options:
        lines.append(f"  ... {len(options) - max_options} more")

    return "\n".join(lines)


def load_obs_from_vis(path: Path, step: int) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    obs = data[step].get("obs")
    if not isinstance(obs, dict):
        raise ValueError(f"No observation dict at step {step}")
    return obs


def main() -> None:
    parser = argparse.ArgumentParser(description="Pretty print an observation from vis.json.")
    parser.add_argument("--file", default="vis.json")
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--max-options", type=int, default=20)
    args = parser.parse_args()

    db = load_default_database()
    obs = load_obs_from_vis(ROOT / args.file, args.step)
    print(inspect_observation(obs, db, args.max_options))


if __name__ == "__main__":
    main()
