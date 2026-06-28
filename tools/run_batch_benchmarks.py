import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.evaluation import run_benchmark


def run_batch(games: int, runs: int, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for index in range(runs):
        summary = run_benchmark(games)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"benchmark_{index + 1:02d}_{timestamp}.json"
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        summaries.append({"file": str(path), **summary})
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a batch of benchmark games and save each result")
    parser.add_argument("--games", type=int, default=2, help="Games to play per benchmark run")
    parser.add_argument("--runs", type=int, default=3, help="How many benchmark runs to execute")
    parser.add_argument("--output-dir", type=str, default="outputs/benchmarks", help="Directory to store benchmark JSON files")
    args = parser.parse_args()

    summaries = run_batch(args.games, args.runs, Path(args.output_dir))
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
