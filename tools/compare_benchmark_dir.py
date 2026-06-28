import argparse
import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.compare_benchmarks import compare_summaries


def collect_benchmark_files(directory: Path) -> List[Path]:
    return sorted(directory.glob("*.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare all benchmark JSON files in a directory")
    parser.add_argument("directory", help="Directory containing benchmark JSON files")
    args = parser.parse_args()

    directory = Path(args.directory)
    files = collect_benchmark_files(directory)
    if not files:
        print(json.dumps({"runs": [], "message": "No benchmark files found"}, indent=2))
        return

    summary = compare_summaries(files)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
