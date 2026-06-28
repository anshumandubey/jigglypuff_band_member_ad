from main import AttackPlan, OptionType, SelectContext, apply_search_policy
from tools.search_policy import shallow_search_policy


def test_shallow_search_policy_returns_action_list():
    result = shallow_search_policy({"select": None})
    assert result == []


def test_apply_search_policy_prefers_plan_ready_attacks():
    class FakeOption:
        def __init__(self, option_type):
            self.type = option_type

    class FakeSelect:
        def __init__(self):
            self.option = [FakeOption(OptionType.PLAY), FakeOption(OptionType.ATTACK)]

    plan = AttackPlan()
    plan.attack_index = 0
    plan.target = 0

    adjusted = apply_search_policy(
        FakeSelect(),
        [5.0, 5.0],
        SelectContext.MAIN,
        plan,
        None,
        None,
        None,
    )

    assert adjusted[1] > adjusted[0]
