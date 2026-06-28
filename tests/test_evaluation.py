from tools.evaluation import classify_action, summarize_results


def test_summarize_results_reports_win_rate_and_average_turns():
    results = [0, 1, 0, 1, 0]
    summary = summarize_results(results, turns=[12, 20, 14, 24, 16])

    assert summary["games"] == 5
    assert summary["wins"] == 3
    assert summary["win_rate"] == 0.6
    assert summary["avg_turns"] == 17.2
    assert summary["player_0_wins"] == 3
    assert summary["player_1_wins"] == 2


def test_summarize_results_tracks_prize_difference():
    summary = summarize_results([0, 1], turns=[10, 12], prize_differences=[2, -1])

    assert summary["avg_prize_difference"] == 0.5
    assert summary["best_prize_difference"] == 2
    assert summary["worst_prize_difference"] == -1


def test_summarize_results_tracks_action_types_and_failures():
    summary = summarize_results(
        [0, 1],
        turns=[10, 12],
        prize_differences=[2, -1],
        action_types=["attack", "attach"],
        failures=[None, "timeout"],
    )

    assert summary["action_type_counts"]["attack"] == 1
    assert summary["action_type_counts"]["attach"] == 1
    assert summary["failures"] == {"timeout": 1}


def test_classify_action_uses_context_for_switches():
    assert classify_action(context=41, option_types=[1], action_indices=[0]) == "setup"
    assert classify_action(context=0, option_types=[1], action_indices=[0]) == "play"
