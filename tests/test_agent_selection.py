from cg.api import EnergyType

from main import (
    Dusk_Ball,
    estimate_attack_score,
    retreat_priority_score,
    setup_priority_score,
    supporter_priority_score,
    bench_priority_score,
    draw_priority_score,
)


def test_knockout_attack_scores_higher_than_non_knockout():
    knockout = estimate_attack_score(
        base_damage=130,
        target_hp=100,
        weakness=None,
        resistance=None,
        prize_value=2,
        energy_count=2,
        base_score=40,
    )
    non_knockout = estimate_attack_score(
        base_damage=80,
        target_hp=100,
        weakness=None,
        resistance=None,
        prize_value=0,
        energy_count=1,
        base_score=0,
    )

    assert knockout > non_knockout


def test_weakness_increases_attack_score():
    normal = estimate_attack_score(
        base_damage=100,
        target_hp=120,
        weakness=None,
        resistance=None,
        prize_value=1,
        energy_count=1,
        base_score=0,
    )
    weak = estimate_attack_score(
        base_damage=100,
        target_hp=120,
        weakness=EnergyType.FIGHTING,
        resistance=None,
        prize_value=1,
        energy_count=1,
        base_score=0,
    )

    assert weak > normal


def test_setup_priority_prefers_riolu_early():
    early_riolu = setup_priority_score(
        pokemon_id=677,
        turn=1,
        has_active_pokemon=False,
        bench_count=0,
        hand_energy_count=1,
    )
    early_makuhita = setup_priority_score(
        pokemon_id=673,
        turn=1,
        has_active_pokemon=False,
        bench_count=0,
        hand_energy_count=1,
    )

    assert early_riolu > early_makuhita


def test_retreat_priority_rises_when_active_is_damaged():
    damaged = retreat_priority_score(active_hp=60, max_hp=120, bench_count=1, prize_count=2)
    healthy = retreat_priority_score(active_hp=120, max_hp=120, bench_count=1, prize_count=2)

    assert damaged > healthy


def test_supporter_priority_prefers_timing_when_attack_plan_is_ready():
    ready = supporter_priority_score(plan_ready=True, has_supporter=False, hand_supporters=2, prize_count=2)
    not_ready = supporter_priority_score(plan_ready=False, has_supporter=False, hand_supporters=2, prize_count=2)

    assert ready > not_ready


def test_bench_priority_prefers_attacking_pokemon_with_energy():
    energized = bench_priority_score(pokemon_id=678, energy_count=2, bench_count=1, is_active=False)
    weak = bench_priority_score(pokemon_id=673, energy_count=0, bench_count=1, is_active=False)

    assert energized > weak


def test_draw_priority_prefers_search_when_bench_is_sparse():
    early = draw_priority_score(card_id=Dusk_Ball, hand_size=7, bench_count=1, prize_count=2, has_active_pokemon=True)
    late = draw_priority_score(card_id=Dusk_Ball, hand_size=2, bench_count=3, prize_count=5, has_active_pokemon=True)

    assert early > late
