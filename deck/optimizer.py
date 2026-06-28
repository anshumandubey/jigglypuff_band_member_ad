from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cards import CardDatabase, EnergyCard, PokemonCard, TrainerCard, load_default_database
from deck.loader import load_deck_ids
from main import AgentConfig, AGENT_CONFIG, agent, set_active_deck
from cg.game import battle_finish, battle_select, battle_start


def max_allowed_count(card_id: int) -> int:
    return 10 if card_id == 6 else 4


def deck_synergy_score(deck_ids: Sequence[int]) -> float:
    """Estimate how well a deck matches the current core strategy."""
    counts = Counter(deck_ids)
    score = 0.0

    target_counts = {
        673: 2,
        674: 2,
        675: 2,
        676: 3,
        677: 3,
        678: 4,
        1102: 4,
        1123: 2,
        1141: 4,
        1142: 4,
        1152: 4,
        1159: 1,
        1182: 2,
        1192: 4,
        1227: 4,
        1252: 2,
        6: 13,
    }

    for card_id, target in target_counts.items():
        score += -abs(counts.get(card_id, 0) - target) * 8

    score += counts.get(6, 0) * 0.1
    score += counts.get(678, 0) * 0.4
    score += counts.get(1102, 0) * 0.2
    return score


def mutate_deck(deck_ids: Sequence[int], replacements: Iterable[tuple[int, int]]) -> list[int]:
    """Return a new deck with a small set of card replacements applied."""
    mutated = list(deck_ids)
    for old_id, new_id in replacements:
        if old_id == new_id:
            continue
        if old_id not in mutated:
            continue
        if mutated.count(new_id) >= max_allowed_count(new_id):
            continue
        idx = mutated.index(old_id)
        mutated[idx] = new_id
    return mutated


def build_candidate_pool(deck_ids: Sequence[int], db: CardDatabase | None = None) -> list[int]:
    """Build a small pool of plausible replacement cards for the current deck."""
    database = db or load_default_database()
    pool = list(dict.fromkeys(deck_ids))
    relevant_ids: set[int] = set(pool)

    keywords = {
        "makuhita",
        "hariyama",
        "riolu",
        "lucario",
        "solrock",
        "lunatone",
        "carmine",
        "lillie",
        "boss",
        "dusk ball",
        "switch",
        "premium power pro",
        "fighting gong",
        "poke pad",
        "hero cape",
        "gravity mountain",
        "energy",
    }

    for card in database.all_cards():
        if card.card_id in relevant_ids:
            continue
        name_key = card.name.lower()
        if isinstance(card, PokemonCard):
            if card.card_type == "Fighting" or any(keyword in name_key for keyword in keywords):
                relevant_ids.add(card.card_id)
        elif isinstance(card, TrainerCard):
            if any(keyword in name_key for keyword in keywords):
                relevant_ids.add(card.card_id)
        elif isinstance(card, EnergyCard):
            if card.energy_type == "Fighting" or card.card_type == "Fighting" or "energy" in name_key:
                relevant_ids.add(card.card_id)

    return [card_id for card_id in relevant_ids if card_id != 0][:40]


def evaluate_deck(deck_ids: Sequence[int], games: int = 2) -> dict:
    """Evaluate a deck using a short local benchmark loop."""
    results: list[int] = []
    turns: list[int] = []
    failures: list[str] = []

    for _ in range(games):
        try:
            obs_dict, _ = battle_start(list(deck_ids), list(deck_ids))
            if obs_dict is None:
                failures.append("battle_start")
                continue

            step = 0
            while True:
                result = obs_dict["current"]["result"]
                if result != -1:
                    results.append(result)
                    turns.append(step)
                    break

                action = agent(obs_dict)
                obs_dict = battle_select(action)
                step += 1
        except Exception:
            failures.append("battle_run")
        finally:
            try:
                battle_finish()
            except Exception:
                pass

    wins = sum(1 for result in results if result == 0)
    return {
        "games": len(results),
        "wins": wins,
        "win_rate": wins / len(results) if results else 0.0,
        "avg_turns": sum(turns) / len(turns) if turns else 0.0,
        "deck": list(deck_ids),
        "failures": {failure: failures.count(failure) for failure in sorted(set(failures))},
    }


def self_play_loop(deck_ids: Sequence[int], games: int = 2) -> dict:
    """Run a lightweight self-play benchmark against the current policy."""
    return evaluate_deck(deck_ids, games=games)


def build_agent_config_variants(base_config: AgentConfig, count: int = 3) -> list[AgentConfig]:
    """Create a small set of nearby policy variants for tuning."""
    variants: list[AgentConfig] = []
    for index in range(count):
        variants.append(
            AgentConfig(
                attack_knockout_bonus=base_config.attack_knockout_bonus + (index * 250),
                attack_prize_bonus=base_config.attack_prize_bonus + (index * 50),
                supporter_ready_bonus=base_config.supporter_ready_bonus + (index * 5),
                draw_dusk_ball=base_config.draw_dusk_ball + (index * 2),
                search_attack_plan_bonus=base_config.search_attack_plan_bonus + (index * 2),
            )
        )
    return variants


def evaluate_agent_config(config: AgentConfig, deck_ids: Sequence[int], games: int = 2) -> dict:
    """Evaluate a policy configuration on a specific deck using the existing benchmark loop."""
    previous_config = AGENT_CONFIG
    import main

    main.AGENT_CONFIG = config
    try:
        return evaluate_deck(deck_ids, games=games)
    finally:
        main.AGENT_CONFIG = previous_config


def optimize_agent_loop(
    deck_ids: Sequence[int] | None = None,
    games_per_candidate: int = 2,
    iterations: int = 3,
    candidate_limit: int = 4,
) -> dict:
    """Tune the agent policy parameters against the current deck with a simple local loop."""
    base_deck = list(deck_ids or load_deck_ids("deck.csv"))
    set_active_deck(base_deck)
    base_summary = evaluate_agent_config(AGENT_CONFIG, base_deck, games=games_per_candidate)
    best_config = AGENT_CONFIG
    best_summary = base_summary

    for _ in range(iterations):
        variants = build_agent_config_variants(best_config, count=max(2, candidate_limit))
        for config in variants:
            summary = evaluate_agent_config(config, base_deck, games=games_per_candidate)
            if summary["win_rate"] > best_summary["win_rate"] or (
                summary["win_rate"] == best_summary["win_rate"] and summary["avg_turns"] < best_summary["avg_turns"]
            ):
                best_summary = summary
                best_config = config

    return {
        "best_summary": best_summary,
        "best_config": best_config,
        "iterations": iterations,
    }


def optimize_deck_loop(
    deck_ids: Sequence[int] | None = None,
    games_per_candidate: int = 2,
    iterations: int = 3,
    candidate_limit: int = 8,
    seed: int = 0,
    write_to_disk: bool = False,
    output_path: str | Path | None = None,
) -> dict:
    """Run a simple hill-climbing deck optimization loop using local battles."""
    base_deck = list(deck_ids or load_deck_ids("deck.csv"))
    rng = random.Random(seed)
    db = load_default_database()
    candidate_pool = build_candidate_pool(base_deck, db)

    best_deck = base_deck.copy()
    best_summary = evaluate_deck(best_deck, games=games_per_candidate)

    current_deck = base_deck.copy()
    for iteration in range(iterations):
        baseline = self_play_loop(current_deck, games=max(1, games_per_candidate // 2))
        proposals: list[tuple[float, list[int]]] = []
        for old_id in dict.fromkeys(current_deck):
            if len(proposals) >= candidate_limit:
                break
            for new_id in rng.sample(candidate_pool, min(3, len(candidate_pool))):
                if new_id == old_id:
                    continue
                proposal = mutate_deck(current_deck, [(old_id, new_id)])
                proposals.append((deck_synergy_score(proposal), proposal))
                if len(proposals) >= candidate_limit:
                    break
            if len(proposals) >= candidate_limit:
                break

        proposals.sort(key=lambda item: item[0], reverse=True)
        if not proposals:
            break

        for _, proposal in proposals[: max(1, candidate_limit // 2)]:
            summary = evaluate_deck(proposal, games=games_per_candidate)
            if summary["win_rate"] > baseline["win_rate"] or (
                summary["win_rate"] == baseline["win_rate"] and summary["avg_turns"] < baseline["avg_turns"]
            ):
                best_summary = summary
                best_deck = proposal
                current_deck = proposal
                break

        if current_deck == best_deck and iteration == iterations - 1:
            break

        for _, proposal in proposals[: max(1, candidate_limit // 2)]:
            summary = evaluate_deck(proposal, games=games_per_candidate)
            if summary["win_rate"] > best_summary["win_rate"] or (
                summary["win_rate"] == best_summary["win_rate"] and summary["avg_turns"] < best_summary["avg_turns"]
            ):
                best_summary = summary
                best_deck = proposal
                current_deck = proposal
                break

    if write_to_disk:
        target_path = Path(output_path or "deck.csv")
        target_path.write_text("\n".join(str(card_id) for card_id in best_deck) + "\n", encoding="utf-8")

    return {
        "best_summary": best_summary,
        "best_deck": best_deck,
        "iterations": iterations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize the local deck through a small search loop")
    parser.add_argument("--deck", type=str, default="deck.csv", help="Deck file to optimize")
    parser.add_argument("--games", type=int, default=2, help="Games per candidate evaluation")
    parser.add_argument("--iterations", type=int, default=3, help="Hill-climbing iterations")
    parser.add_argument("--candidate-limit", type=int, default=8, help="How many replacements to try each iteration")
    parser.add_argument("--output", type=str, default=None, help="Optional path to save the best deck")
    parser.add_argument("--write", action="store_true", help="Write the best deck back to deck.csv")
    args = parser.parse_args()

    base_deck = load_deck_ids(args.deck)
    result = optimize_deck_loop(
        deck_ids=base_deck,
        games_per_candidate=args.games,
        iterations=args.iterations,
        candidate_limit=args.candidate_limit,
        write_to_disk=args.write or bool(args.output),
        output_path=args.output or args.deck,
    )
    print(json.dumps(result["best_summary"], indent=2))
    if args.write or args.output:
        print(f"Wrote optimized deck to {args.output or args.deck}")


if __name__ == "__main__":
    main()
