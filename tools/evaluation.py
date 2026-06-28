import argparse
import json
import sys
from pathlib import Path
from collections import Counter
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cg.game import battle_finish, battle_select, battle_start
from main import agent


def classify_action(context: int, option_types: List[int], action_indices: List[int]) -> str:
    """Classify a benchmarked action into a simple category."""
    if context == 41:
        return "setup"
    if context in {0, 1, 2, 3, 4, 7, 8, 21, 22, 30, 43}:
        if len(action_indices) > 1 or 1 in option_types:
            return "play"
        return "attack"
    return "other"


def summarize_results(
    results: List[int],
    turns: Optional[List[int]] = None,
    prize_differences: Optional[List[int]] = None,
    action_types: Optional[List[str]] = None,
    failures: Optional[List[Optional[str]]] = None,
) -> dict:
    """Summarize a batch of game outcomes into simple statistics."""
    if not results:
        return {
            "games": 0,
            "wins": 0,
            "win_rate": 0.0,
            "avg_turns": 0.0,
            "avg_prize_difference": 0.0,
            "best_prize_difference": 0,
            "worst_prize_difference": 0,
            "action_type_counts": {},
            "failures": {},
            "player_0_wins": 0,
            "player_1_wins": 0,
        }

    wins = sum(1 for result in results if result == 0)
    turns_list = turns or [0] * len(results)
    avg_turns = sum(turns_list) / len(turns_list) if turns_list else 0.0

    prize_list = prize_differences or [0] * len(results)
    avg_prize_difference = sum(prize_list) / len(prize_list) if prize_list else 0.0
    action_counts = Counter(action_types or [])
    failure_counts = Counter(
        failure for failure in (failures or []) if failure is not None
    )
    return {
        "games": len(results),
        "wins": wins,
        "win_rate": wins / len(results),
        "avg_turns": avg_turns,
        "avg_prize_difference": avg_prize_difference,
        "best_prize_difference": max(prize_list) if prize_list else 0,
        "worst_prize_difference": min(prize_list) if prize_list else 0,
        "action_type_counts": dict(action_counts),
        "failures": dict(failure_counts),
        "player_0_wins": wins,
        "player_1_wins": len(results) - wins,
    }


def run_benchmark(games: int = 10) -> dict:
    """Run a small batch of local games using the current agent."""
    results: List[int] = []
    turns: List[int] = []
    prize_differences: List[int] = []
    action_types: List[str] = []
    failures: List[Optional[str]] = []

    for _ in range(games):
        deck = [int(line.strip()) for line in open("deck.csv", encoding="utf-8") if line.strip()]
        obs_dict, start_data = battle_start(deck, deck)
        if obs_dict is None:
            raise RuntimeError(f"Battle failed to start: {start_data}")

        step = 0
        while True:
            result = obs_dict["current"]["result"]
            if result != -1:
                results.append(result)
                turns.append(step)
                prize_differences.append(0)
                action_types.append("attack")
                failures.append(None)
                break

            action = agent(obs_dict)
            obs_dict = battle_select(action)
            step += 1

    battle_finish()
    return summarize_results(results, turns, prize_differences, action_types, failures)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small local benchmark for the agent")
    parser.add_argument("--games", type=int, default=10, help="Number of benchmark games to run")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save the benchmark summary as JSON",
    )
    args = parser.parse_args()

    summary = run_benchmark(args.games)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Saved benchmark summary to {output_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
