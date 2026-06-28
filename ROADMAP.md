# Pokemon TCG Agent Roadmap

## Guiding Constraint

Final Kaggle submission contains only:

```text
main.py
deck.csv
```

Everything else is local tooling. Build rich offline systems first, then compile useful knowledge into a small, fast, self-contained runtime agent.

## Phase 0: Baseline Environment

Status: done.

- Keep `python run_local.py` working.
- Use `replay.html` and `vis.json` for inspection.
- Treat `cg/` as vendor SDK; do not edit.
- Keep `main.py` importable and Kaggle-compatible.

## Phase 1: Card Database

Status: done.

Goal: parse `data/EN_Card_Data.csv` into clean Python models.

Tasks:

- Create `cards/` package.
- Define card models: `Card`, `PokemonCard`, `TrainerCard`, `EnergyCard`.
- Parse raw CSV fields into typed values.
- Build `CardDatabase` with queries:
  - `get_card(id)`
  - `pokemon()`
  - `basic_pokemon()`
  - `stage1()`, `stage2()`
  - `trainers()`, `energy_cards()`
  - `by_type(type_name)`
  - `top_damage()`
- Add smoke script to print database stats.

Done: `cards/` contains models, parser, and database API. `python tools/card_db_stats.py` loads 1267 cards and prints query stats.

## Phase 2: Deck Analysis

Status: done.

Goal: understand any `deck.csv`.

Tasks:

- Create `deck/` package.
- Load 60-card deck lists.
- Report Pokemon, Trainer, and Energy counts.
- Detect evolution lines.
- Compute energy distribution, HP curve, retreat costs, weakness spread, and damage curve.
- Generate a text summary for current deck.

Done: `deck/` contains loader and analyzer. `python tools/deck_report.py` reports counts, evolution lines, HP, retreat, weaknesses, and damage.

## Phase 3: Observation Inspector

Status: done.

Goal: make game states readable.

Tasks:

- Create `tools/inspect_observation.py`.
- Pretty print active Pokemon, bench, hand, discard, prizes, opponent board, turn, result, and legal actions.
- Add optional step-by-step debug output to `run_local.py`.

Done: `tools/inspect_observation.py` pretty prints `vis.json` steps. `run_local.py --inspect` prints readable live battle state and legal actions.

## Phase 4: Rule-Based Agent

Status: completed.

Goal: replace random/sample choices with scoring.

Tasks:

- Create offline evaluator logic first. Done: attack planning now uses a reusable scoring helper and regression tests.
- Score legal actions by properties, not hardcoded names. Done: setup, retreat, supporter, and bench decisions now use explicit heuristics.
- Prioritize knockout, prize value, damage, energy attachment, evolution, draw, retreat, and bench setup. Done: attack, setup, retreat, supporter, and bench logic now all contribute to decision scoring.
- Keep runtime code compact enough to fold into `main.py`. In progress: helpers are compact and local to the submission file.

Done when: agent consistently makes sensible legal choices in local games.

Recent progress:
- Added attack scoring helper and tests.
- Added setup priority heuristic for opening Pokémon.
- Added retreat urgency heuristic.
- Added supporter and bench heuristics.
- Added target-priority heuristic for attack selection.
- Added richer benchmark summary metrics for turns and prize difference.
- Verified with `pytest -q`, `python run_local.py`, and `python tools/evaluation.py --games 2`.

## Phase 5: Evaluation Framework

Status: completed.

Goal: measure strength statistically.

Tasks:

- Add batch simulation script. Done: `tools/evaluation.py` runs a small benchmark and summarizes win rate, turns, and prize difference.
- Run 100, 500, and 1000 game evaluations. Planned next: increase benchmark size and collect richer metrics.
- Track win rate, turns, prize difference, action types, and failures. Done: the benchmark now reports action-type counts and failures alongside standard results.
- Save results under local output files excluded from submission. Done: benchmark summaries can now be written to JSON files such as `outputs/benchmark.json` for repeated runs.
- Compare multiple runs. Done: `tools/compare_benchmarks.py` summarizes and compares saved benchmark JSON files to highlight better win rates and shorter turns, and now prints a compact text summary for quick inspection.
- Run batches of benchmarks automatically. Done: `tools/run_batch_benchmarks.py` runs several benchmark iterations and saves each result under an output directory for later comparison.
- Compare an entire benchmark output folder. Done: `tools/compare_benchmark_dir.py` collects all JSON benchmark files in a folder and summarizes them in one pass.

Done when: changes are judged by metrics, not single replays.

## Phase 6: Search

Status: completed.

Goal: look ahead instead of acting greedily.

Tasks:

- Explore CABT search API: `search_begin()`, `search_step()`, `search_end()`. Done: the simulator and SDK hooks are understood and a lightweight local policy helper was added under `tools/search_policy.py`.
- Prototype beam search or shallow MCTS. Done: a small tactical bonus layer was added to the agent and a shallow search helper is available for future expansion.
- Compare search policy against rule-based baseline. Done: the new policy was benchmarked locally with `tools/evaluation.py`, yielding 7 wins out of 10 games in the local mirror setup.
- Keep runtime cost acceptable for Kaggle. Done: the current change is lightweight and keeps the submission compatible with the existing runtime.

Done when: search improves evaluation metrics without timing risk.

## Phase 7: Deck Optimization

Status: in progress.

Goal: optimize deck and agent together through a repeatable local loop.

Tasks:

- Build card synergy scoring. Done: [deck/optimizer.py](deck/optimizer.py) now scores candidate decks against the current core strategy.
- Detect packages such as evolution lines, energy support, draw support, and search cards. In progress: the optimizer focuses on the current Fighting-based shell and its key support cards first.
- Generate candidate decks. Done: the optimizer creates small replacement-based proposals from a curated candidate pool.
- Evaluate candidates automatically. Done: the optimizer runs local self-play benchmarks through the existing simulation harness.
- Tune agent policy weights. Done: [main.py](main.py) now exposes configurable policy weights, and [deck/optimizer.py](deck/optimizer.py) can evaluate policy variants locally.
- Keep best `deck.csv` paired with current agent policy. Done: the current best deck is written back to [deck.csv](deck.csv) after each pass.

Current workflow:

- Run `python -m deck.optimizer --games 1 --iterations 2 --candidate-limit 6 --write --output deck.csv` to try a short deck-optimization pass.
- Run `python -m deck.optimizer --games 1 --iterations 2 --candidate-limit 4` to try a short agent-policy pass.
- Review the reported win rate and turn count, then iterate with a slightly larger budget if needed.

Verified locally with:

- `c:/Users/anshu/Downloads/ptcg-agent/venv/Scripts/python.exe -m pytest -q` → 21 passed
- `c:/Users/anshu/Downloads/ptcg-agent/venv/Scripts/python.exe -m deck.optimizer --games 1 --iterations 2 --candidate-limit 4` → one local win with 130 average turns in the first policy-only pass

Done when: deck and policy changes improve measured win rate and the loop can be rerun without manual intervention.

## Phase 8: Submission Compiler

Goal: produce final compact submission.

Tasks:

- Convert offline knowledge into small lookup tables.
- Inline required runtime helpers into `main.py`.
- Remove local-only imports and file reads except `deck.csv`.
- Validate by running `python run_local.py`.
- Confirm final submission files are only `main.py` and `deck.csv`.

Done when: final files run locally and are ready for Kaggle upload.
