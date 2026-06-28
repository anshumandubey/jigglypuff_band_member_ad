# Pokemon TCG AI Battle

This repository contains a local development environment and an evolving agent for the Kaggle Pokemon TCG AI Battle competition.

The current project is no longer a sample-only baseline: it includes a heuristic rule-based agent, a local battle harness, benchmarking tools, and a lightweight deck/agent optimization loop.

---

## What is in this repo

- [main.py](main.py): Kaggle-compatible submission entrypoint and the main heuristic agent
- [deck.csv](deck.csv): the current 60-card deck used by local battles
- [run_local.py](run_local.py): local simulator wrapper for testing the agent
- [tools/evaluation.py](tools/evaluation.py): local benchmark runner for win-rate and turn summaries
- [deck/optimizer.py](deck/optimizer.py): lightweight deck and policy optimizer loop
- [tests/](tests/): regression tests for scoring logic, evaluation helpers, and optimizer behavior
- [cg/](cg/): official competition SDK files

---

## Current status

### Implemented

- Local Python environment setup
- Official SDK integration
- Local battle simulation and replay generation
- A heuristic agent with scoring for:
  - attacks
  - setup plays
  - retreat timing
  - supporter plays
  - bench placement
  - draw/search actions
- Local evaluation and benchmarking
- A simple optimizer loop for both deck choice and policy weights

### Current workflow

The agent is tested locally before submission using the simulator and benchmark scripts.

---

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Run a local battle

```powershell
python run_local.py
```

This will run a local battle, call the agent, and regenerate replay and visualization artifacts.

---

## Run a benchmark

```powershell
python tools/evaluation.py --games 10 --output outputs/benchmark.json
```

---

## Optimize the deck and policy

A lightweight optimizer is available:

```powershell
python -m deck.optimizer --games 2 --iterations 4 --candidate-limit 6
```

This evaluates small candidate changes and keeps the best-performing options from local battles.

---

## Project structure

```text
ptcg-agent/
├── cg/                        # Official competition SDK
├── cards/                     # Card database models and parser
├── deck/                      # Deck loader and analysis helpers
├── tests/                     # Regression tests
├── tools/                     # Evaluation and analysis utilities
├── deck.csv                   # Current deck list
├── main.py                    # Kaggle submission entry point
├── run_local.py               # Local simulator wrapper
├── requirements.txt
└── ROADMAP.md                 # Development roadmap
```

---

## Notes

- The repository is designed so local experimentation is done offline first.
- The Kaggle submission remains centered on [main.py](main.py) and [deck.csv](deck.csv).
- Large media/data assets are intentionally excluded from the repository history to keep the project lightweight.

