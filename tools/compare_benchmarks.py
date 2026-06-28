import argparse
import json
from pathlib import Path
from typing import List


def load_summary(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_summaries(paths: List[Path]) -> dict:
    results = []
    for path in paths:
        results.append({"name": path.stem, "path": str(path), **load_summary(path)})

    best_win_rate = max(results, key=lambda item: item["win_rate"])
    best_avg_turns = min(results, key=lambda item: item["avg_turns"])
    return {
        "runs": results,
        "best_win_rate": best_win_rate,
        "best_avg_turns": best_avg_turns,
        "summary_text": (
            f"Best win rate: {best_win_rate['name']} ({best_win_rate['win_rate']:.2%})\n"
            f"Fastest average turns: {best_avg_turns['name']} ({best_avg_turns['avg_turns']:.1f})"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare saved benchmark JSON summaries")
    parser.add_argument("paths", nargs="+", help="Benchmark JSON files to compare")
    args = parser.parse_args()

    summaries = compare_summaries([Path(path) for path in args.paths])
    print(json.dumps(summaries, indent=2))
    print("\nSummary:")
    print(summaries["summary_text"])


if __name__ == "__main__":
    main()
