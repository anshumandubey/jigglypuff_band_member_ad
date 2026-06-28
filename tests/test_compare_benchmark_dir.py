from pathlib import Path

from tools.compare_benchmark_dir import collect_benchmark_files


def test_collect_benchmark_files_finds_json_outputs(tmp_path: Path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "b.json").write_text("{}", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    files = collect_benchmark_files(tmp_path)

    assert [path.name for path in files] == ["a.json", "b.json"]
