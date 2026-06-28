import deck.optimizer as optimizer
from deck.optimizer import mutate_deck


def test_mutate_deck_replaces_cards_and_preserves_length():
    deck = [1] * 60

    mutated = mutate_deck(deck, [(1, 2)])

    assert len(mutated) == 60
    assert mutated.count(2) == 1
    assert mutated.count(1) == 59


def test_mutate_deck_can_apply_multiple_replacements():
    deck = [1] * 60

    mutated = mutate_deck(deck, [(1, 2), (1, 3)])

    assert len(mutated) == 60
    assert mutated.count(2) == 1
    assert mutated.count(3) == 1
    assert mutated.count(1) == 58


def test_evaluate_deck_reports_failed_battle_start(monkeypatch):
    monkeypatch.setattr(optimizer, "battle_start", lambda *args, **kwargs: (None, None))

    summary = optimizer.evaluate_deck([1] * 60, games=1)

    assert summary["games"] == 0
    assert summary["win_rate"] == 0.0
    assert summary["failures"] == {"battle_start": 1}
