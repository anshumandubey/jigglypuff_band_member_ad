# Repository Guidelines

## Project Structure & Module Organization

This repository is a local development workspace for the Kaggle Pokemon TCG AI Battle competition. The main submission logic lives in `main.py`; Kaggle calls `agent(obs_dict)` and expects a list of selected option indices. `run_local.py` runs a local mirror match using the current `deck.csv`, then writes `replay.html` and `vis.json` for debugging. The `cg/` package is the official competition SDK and includes native libraries for Windows, Linux, and macOS; treat it as vendor code and avoid modifying it. Competition data is stored under `data/`, including card CSVs, PDFs, and the sample submission.

## Build, Test, and Development Commands

Create and activate a local environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run a local battle:

```powershell
python run_local.py
```

This exercises `main.agent()`, prints each decision step, and regenerates `replay.html` and `vis.json`. Launch notebooks or inspect data with:

```powershell
jupyter lab
```

There is no separate build step; this is a Python script-based project.

## Coding Style & Naming Conventions

Use standard Python formatting with 4-space indentation. Keep public agent behavior centered in `main.py`, and move reusable helpers into small functions with clear names such as `get_card`, `prize_count`, or `pokemon_score`. Prefer typed signatures where practical, especially for helpers that consume `cg.api` classes. Constants for card IDs currently use descriptive deck names such as `Mega_Lucario_ex`; keep new card constants readable and close to deck logic.

## Testing Guidelines

No first-party test suite is currently present. Use `python run_local.py` as the minimum smoke test after agent changes, and inspect both terminal output and generated replay artifacts. For future tests, add them under `tests/` with names like `test_agent_selection.py`, and focus on deterministic helpers before simulating full games.

## Commit & Pull Request Guidelines

This checkout does not include Git history, so no project-specific commit convention is available. Use short imperative commit messages such as `Improve attack target scoring` or `Add local evaluation script`. Pull requests should describe the gameplay behavior changed, list local commands run, and mention any generated artifacts reviewed. Include screenshots only when replay or visualizer output changes materially.

## Agent-Specific Instructions

Do not edit `cg/` or generated files (`replay.html`, `vis.json`) unless the task explicitly targets them. Keep `deck.csv` exactly 60 card IDs, one per line. When changing `main.py`, preserve Kaggle compatibility: avoid local-only paths except guarded fallbacks, and keep `agent(obs_dict)` importable without running a local battle.
