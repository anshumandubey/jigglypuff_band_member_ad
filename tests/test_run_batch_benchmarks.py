from pathlib import Path

from tools.run_batch_benchmarks import run_batch


def test_run_batch_writes_benchmark_files(tmp_path: Path):
    summaries = run_batch(games=1, runs=2, output_dir=tmp_path)

    assert len(summaries) == 2
    assert len(list(tmp_path.glob("*.json"))) == 2
