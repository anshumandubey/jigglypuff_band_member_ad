from __future__ import annotations

from pathlib import Path


def load_deck_ids(path: str | Path) -> list[int]:
    deck_path = Path(path)
    ids = [int(line.strip()) for line in deck_path.read_text().splitlines() if line.strip()]
    if len(ids) != 60:
        raise ValueError(f"Deck must contain 60 cards, found {len(ids)}")
    return ids
