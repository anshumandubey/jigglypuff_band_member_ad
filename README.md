# Pokemon TCG AI Battle

Local development environment for the Kaggle **Pokemon TCG AI Battle** competition.

---

# Project Status

## ✅ Completed

* Local Python environment configured
* Official `cg` SDK extracted from the sample submission
* Local battle simulation working
* Custom `run_local.py` to simulate games locally
* Replay generation
* Visualization JSON generation (`vis.json`)
* Basic debugging utilities

Current agent is still the sample/random agent.

---

# Project Structure

```
ptcg-agent/
│
├── cg/                        # Official competition SDK
│
├── data/                      # Competition data
│
├── deck.csv                   # Current deck (60 card IDs)
├── main.py                    # Kaggle submission entry point
├── run_local.py               # Local simulator
│
├── replay.html                # Generated after each run
├── vis.json                   # Generated after each run
├── visualiser.html            # Local visualiser
│
├── debug_game.py              # Debugging utilities
├── explore.py                 # SDK exploration
├── inspect_game.py            # API inspection
│
├── beginner-guide-from-deck-list-to-first-valid-sub.ipynb
│
├── requirements.txt
└── initial_setup.zip
```

---

# Environment Setup

Create a virtual environment.

```
python -m venv venv
```

Activate it.

Windows PowerShell:

```
venv\Scripts\Activate.ps1
```

Install requirements.

```
pip install -r requirements.txt
```

---

# Running a Local Battle

```
python run_local.py
```

The script will:

* Start a local battle
* Call `main.agent()` whenever a decision is required
* Continue until the battle finishes
* Save:

```
replay.html
vis.json
```

---

# Viewing the Replay

Open

```
replay.html
```

in a browser.

---

# Viewing vis.json

The generated `vis.json` can be opened using the CABT visualizer.

It contains:

* every observation
* every selected action
* complete battle history

Useful for debugging and replay analysis.

---

# main.py

`main.py` is the Kaggle submission file.

Kaggle repeatedly calls

```python
agent(obs_dict)
```

Your agent returns a list of selected option indices.

---

# deck.csv

Contains the 60-card deck.

One card ID per line.

---

# cg/

Official competition SDK.

Contains:

* Python API
* Windows DLL
* Linux shared libraries
* macOS library

Do **not** modify these files.

---

# Useful Files

## run_local.py

Runs a complete local battle.

Generates:

* replay.html
* vis.json

---

## debug_game.py

Used to inspect observations and legal actions.

---

## explore.py

Used while exploring the SDK.

---

## inspect_game.py

Used to inspect the SDK API.

---

# Current Development Status

Current implementation:

* Sample/random agent
* Local simulator working
* Replay generation working
* Visualization generation working

Next milestone:

* Replace random decision making with a rule-based agent.

---

# Future Roadmap

## Phase 1

* Build helper functions
* Inspect observations
* Inspect board state

## Phase 2

* Rule-based agent
* Better attack selection
* Better retreat logic
* Better evolution logic

## Phase 3

* Local evaluation script
* Automated benchmarking
* Win-rate statistics

## Phase 4

* Advanced search
* MCTS / Beam Search
* Tournament-ready agent

---

# Notes

Current local testing uses the official `cg` SDK rather than Kaggle's online environment.

The same `main.py` should work for both local testing and Kaggle submission.

---

# Current Command Reference

Run local battle

```
python run_local.py
```

Launch Jupyter

```
jupyter lab
```

Activate environment

```
venv\Scripts\Activate.ps1
```
