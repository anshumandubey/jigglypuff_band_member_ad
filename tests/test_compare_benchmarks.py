from pathlib import Path

from tools.compare_benchmarks import compare_summaries


def test_compare_summaries_picks_best_win_rate_and_turns(tmp_path: Path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text('{"games": 2, "win_rate": 0.5, "avg_turns": 100}', encoding="utf-8")
    second.write_text('{"games": 2, "win_rate": 0.75, "avg_turns": 80}', encoding="utf-8")

    summary = compare_summaries([first, second])

    assert summary["best_win_rate"]["win_rate"] == 0.75
    assert summary["best_avg_turns"]["avg_turns"] == 80
    assert len(summary["runs"]) == 2
    assert "Best win rate" in summary["summary_text"]
    assert "Fastest average turns" in summary["summary_text"]
