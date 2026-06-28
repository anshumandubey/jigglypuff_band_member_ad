import main
import deck.optimizer as optimizer
from main import AgentConfig


def test_build_agent_config_variants_changes_values():
    variants = optimizer.build_agent_config_variants(AgentConfig(), count=3)

    assert len(variants) == 3
    assert any(cfg.supporter_ready_bonus != AgentConfig().supporter_ready_bonus for cfg in variants)
    assert any(cfg.draw_dusk_ball != AgentConfig().draw_dusk_ball for cfg in variants)


def test_evaluate_agent_config_restores_previous_config(monkeypatch):
    monkeypatch.setattr(optimizer, "battle_start", lambda *args, **kwargs: (None, None))
    original = main.AGENT_CONFIG

    summary = optimizer.evaluate_agent_config(AgentConfig(supporter_ready_bonus=999), [1] * 60, games=1)

    assert summary["failures"] == {"battle_start": 1}
    assert main.AGENT_CONFIG == original
