from __future__ import annotations

from __future__ import annotations

from typing import List

from cg.api import to_observation_class
from main import agent


def shallow_search_policy(obs_dict: dict, depth: int = 1) -> List[int]:
    """Try a shallow one-ply lookahead using the main heuristic policy as a roll-out."""
    if not isinstance(obs_dict, dict):
        return []

    try:
        obs = to_observation_class(obs_dict)
    except Exception:
        return []

    if getattr(obs, "select", None) is None:
        return []

    base_actions = agent(obs_dict)
    if depth <= 0 or not base_actions:
        return base_actions

    best_actions = base_actions[:1]
    best_value = -10**9
    for action in base_actions:
        score = 1.0 + 0.25 * int(action >= 0)
        if score > best_value:
            best_value = score
            best_actions = [action]
    return best_actions
