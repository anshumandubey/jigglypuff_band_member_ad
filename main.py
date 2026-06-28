import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from cg.api import AreaType, CardType, EnergyType, Observation, SelectContext, OptionType, Card, Pokemon, all_card_data, to_observation_class
from cards.database import CardDatabase, load_default_database

"""
Dynamic Deck PTCG Agent
Battles strategically based on attributes of whichever deck is provided.
"""

def load_deck_from_file(path: str | None = None) -> list[int]:
    """Load the active deck from disk, falling back to Kaggle's agent directory if needed."""
    deck_path = path or "deck.csv"
    if not os.path.exists(deck_path):
        deck_path = "/kaggle_simulations/agent/" + deck_path
    with open(deck_path, "r", encoding="utf-8") as file:
        csv = file.read().split("\n")
    return [int(line) for line in csv[:60] if line.strip()]


my_deck = load_deck_from_file("deck.csv")


@dataclass(frozen=True)
class AgentConfig:
    attack_knockout_bonus: int = 10000
    attack_prize_bonus: int = 2500
    attack_energy_bonus: int = 150
    attack_pressure_scale: float = 1000.0
    attack_prize_pressure_bonus: int = 400
    attack_energy_pressure_bonus: int = 25
    supporter_ready_bonus: int = 60
    supporter_hand_bonus: int = 10
    supporter_prize_bonus: int = 5
    draw_dusk_ball: int = 25
    draw_poke_pad: int = 20
    draw_no_active_bonus: int = 20
    draw_sparse_bench_bonus: int = 15
    draw_prize_bonus: int = 10
    draw_hand_penalty: int = 3
    search_attack_plan_bonus: int = 25
    search_attack_energy_bonus: int = 10
    search_supporter_bonus: int = 20
    search_supporter_initial_bonus: int = 8
    search_dusk_ball_bonus: int = 8
    search_dusk_ball_hand_bonus: int = 2
    search_boss_orders_bonus: int = 10
    search_premium_power_bonus: int = 6
    search_attach_energy_bonus: int = 12
    search_retreat_bonus: int = 10


AGENT_CONFIG = AgentConfig()


def set_active_deck(deck_ids: list[int]) -> None:
    global my_deck
    my_deck = list(deck_ids)


# Fetch card metadata database and create an ID-to-Card lookup table
all_card = all_card_data()
card_table = {c.cardId: c for c in all_card}


def get_card_db() -> CardDatabase:
    try:
        return load_default_database()
    except Exception:
        csv_path = Path("/kaggle_simulations/agent/data/EN_Card_Data.csv")
        if csv_path.exists():
            return CardDatabase.from_csv(csv_path)
        raise


card_db = get_card_db()

# Generic Trainer card constants (no Pokemon hardcoded)
Dusk_Ball = 1102
Switch = 1123
Premium_Power_Pro = 1141
Poke_Pad = 1152
Hero_Cape = 1159
Boss_Orders = 1182
Carmine = 1192
Lillie_Determination = 1227
Gravity_Mountain = 1252
Mega_Signal = 1145
Wondrous_Patch = 1146


def is_main_attacker(card_id: int) -> bool:
    """Determine dynamically if a Pokémon is a primary attacker based on stats."""
    data = card_table.get(card_id)
    if not data or data.cardType != CardType.POKEMON:
        return False
    if data.megaEx or data.ex or data.stage2:
        return True
    if not data.basic and data.hp >= 120:
        return True
    return False


def get_pokemon_max_cost(card_id: int) -> int:
    """Get maximum attack energy cost for a Pokémon card."""
    if card_id in card_db.cards:
        db_card = card_db.get_card(card_id)
        if hasattr(db_card, "moves") and db_card.moves:
            real_moves = [m for m in db_card.moves if not m.name.startswith('[Ability]')]
            if real_moves:
                return max(len(m.cost) for m in real_moves)
    return 2


class AttackPlan:
    attacker = -1
    target = -1
    attack_index = -1
    remain_hp = -1
    energy = False


plan = AttackPlan()
pre_turn = 0
ability_used = False


def estimate_attack_score(
    base_damage: int,
    target_hp: int,
    weakness: EnergyType | None,
    resistance: EnergyType | None,
    prize_value: int,
    energy_count: int,
    attacker_energy_type: EnergyType | None = None,
    base_score: int = 0,
    config: AgentConfig | None = None,
) -> float:
    """Estimate how attractive a given attack is for the current board state."""
    effective_damage = max(0, base_damage)
    if attacker_energy_type is not None:
        if weakness is not None and weakness == attacker_energy_type:
            effective_damage *= 2
        elif resistance is not None and resistance == attacker_energy_type:
            effective_damage = max(0, effective_damage - 30)

    active_config = config or AGENT_CONFIG
    if target_hp <= effective_damage:
        return active_config.attack_knockout_bonus + prize_value * active_config.attack_prize_bonus + energy_count * active_config.attack_energy_bonus + base_score

    pressure = (effective_damage / max(1, target_hp)) * active_config.attack_pressure_scale
    return pressure + prize_value * active_config.attack_prize_pressure_bonus + energy_count * active_config.attack_energy_pressure_bonus + base_score


def setup_priority_score(
    pokemon_id: int,
    turn: int,
    has_active_pokemon: bool,
    bench_count: int,
    hand_energy_count: int,
) -> int:
    """Score which basic Pokémon setup action is best before the main attack plan dynamically."""
    data = card_table.get(pokemon_id)
    if not data or not data.basic:
        score = 10
    else:
        p_name = data.name
        has_big_evo = any(c.evolvesFrom == p_name and is_main_attacker(cid) for cid, c in card_table.items() if cid in my_deck)
        has_any_evo = any(c.evolvesFrom == p_name for cid, c in card_table.items() if cid in my_deck and not c.basic)
        if has_big_evo:
            score = 80
        elif has_any_evo:
            score = 60
        elif data.hp >= 100 or len(data.skills) > 0:
            score = 50
        else:
            score = 30

    if turn <= 2:
        score += 20
    if not has_active_pokemon:
        score += 15
    if bench_count == 0:
        score += 10
    score += min(hand_energy_count, 3) * 5
    return score


def retreat_priority_score(active_hp: int, max_hp: int, bench_count: int, prize_count: int) -> int:
    """Estimate how urgently a retreat should be considered."""
    damage_ratio = 1 - (active_hp / max(1, max_hp))
    score = int(damage_ratio * 100)
    score += max(0, 3 - bench_count) * 10
    score += max(0, prize_count - 2) * 5
    return score


def supporter_priority_score(plan_ready: bool, has_supporter: bool, hand_supporters: int, prize_count: int, config: AgentConfig | None = None) -> int:
    """Score whether a supporter card should be played now."""
    active_config = config or AGENT_CONFIG
    if has_supporter:
        return -1000
    score = 0
    if plan_ready:
        score += active_config.supporter_ready_bonus
    score += hand_supporters * active_config.supporter_hand_bonus
    score += max(0, prize_count - 2) * active_config.supporter_prize_bonus
    return score


def bench_priority_score(pokemon_id: int, energy_count: int, bench_count: int, is_active: bool) -> int:
    """Score how attractive a Pokémon is to place on the bench or keep available dynamically."""
    if is_active:
        return -1000
    score = 0
    data = card_table.get(pokemon_id)
    if data:
        if is_main_attacker(pokemon_id):
            score += 40
        elif not data.basic:
            score += 30
        else:
            p_name = data.name
            has_evo = any(c.evolvesFrom == p_name for cid, c in card_table.items() if cid in my_deck and not c.basic)
            if has_evo:
                score += 25
            else:
                score += 15
    score += energy_count * 8
    score -= max(0, bench_count - 2) * 5
    return score


def target_priority_score(target_hp: int, target_max_hp: int, prize_value: int, is_active: bool) -> int:
    """Score how attractive a given opponent Pokémon is as an attack target."""
    if is_active:
        return 25
    damage_pressure = int((1 - (target_hp / max(1, target_max_hp))) * 100)
    return damage_pressure + prize_value * 40 + 10


def draw_priority_score(card_id: int, hand_size: int, bench_count: int, prize_count: int, has_active_pokemon: bool, config: AgentConfig | None = None) -> int:
    """Score whether searching or drawing cards is attractive in the current state."""
    active_config = config or AGENT_CONFIG
    if card_id == Dusk_Ball:
        score = active_config.draw_dusk_ball
    elif card_id == Poke_Pad:
        score = active_config.draw_poke_pad
    else:
        score = 5

    if not has_active_pokemon:
        score += active_config.draw_no_active_bonus
    if bench_count < 2:
        score += active_config.draw_sparse_bench_bonus
    if prize_count <= 2:
        score += active_config.draw_prize_bonus
    score -= max(0, hand_size - 7) * active_config.draw_hand_penalty
    return score


def get_card(obs: Observation, area: AreaType, index: int, player_index: int) -> Pokemon | Card | None:
    """Helper function to safely extract a Card or Pokemon object from specific zones."""
    ps = obs.current.players[player_index]
    match area:
        case AreaType.DECK:
            return obs.select.deck[index]
        case AreaType.HAND:
            return ps.hand[index]
        case AreaType.DISCARD:
            return ps.discard[index]
        case AreaType.ACTIVE:
            return ps.active[index]
        case AreaType.BENCH:
            return ps.bench[index]
        case AreaType.PRIZE:
            return ps.prize[index]
        case AreaType.STADIUM:
            return obs.current.stadium[index]
        case AreaType.LOOKING:
            return obs.current.looking[index]
        case _:
            return None


def prize_count(pokemon: Pokemon) -> int:
    """Calculates how many Prize cards a Pokémon yields upon being Knocked Out, factoring in modifiers."""
    data = card_table[pokemon.id]
    count = 3 if data.megaEx else 2 if data.ex else 1
    for card in pokemon.energyCards:
        if card.id == 12:  # Legacy Energy
            count -= 1
    for card in pokemon.tools:
        if card.id == 1172 and "Lillie" in data.name:  # Lillie’s Pearl
            count -= 1
    return max(0, count)


def pokemon_score(pokemon: Pokemon) -> int:
    """Heuristically evaluates the tactical worth of targeting a specific Pokémon on the opponent's field."""
    data = card_table[pokemon.id]
    score = prize_count(pokemon) * 1000
    score += len(pokemon.energies) * 150
    score += len(pokemon.tools) * 100
    if data.stage2:
        score += 250
    elif data.stage1:
        score += 130

    id = pokemon.id
    # Utility / high value targets adjustments
    if id in {144, 322, 323, 337}:
        score -= 200
    if id == 112 and len(pokemon.energies) >= 1:  # Munkidori
        score += 300
    score += pokemon.hp
    return score


def search_action_bonus(
    option,
    context: SelectContext,
    plan: AttackPlan,
    state,
    my_state,
    op_state,
    card=None,
    config: AgentConfig | None = None,
) -> float:
    """Small lookahead bonus that prefers actions which improve the current turn plan."""
    active_config = config or AGENT_CONFIG
    if context != SelectContext.MAIN:
        return 0.0

    if option.type == OptionType.ATTACK:
        bonus = 0.0
        if plan.attack_index >= 0 and plan.target >= 0:
            bonus += active_config.search_attack_plan_bonus
        if plan.energy:
            bonus += active_config.search_attack_energy_bonus
        return bonus

    if option.type == OptionType.PLAY and card is not None:
        if card.id in {Carmine, Lillie_Determination}:
            return active_config.search_supporter_bonus if plan.attack_index >= 0 and plan.target >= 0 else active_config.search_supporter_initial_bonus
        if card.id == Dusk_Ball:
            return active_config.search_dusk_ball_bonus if len(my_state.hand) <= 6 else active_config.search_dusk_ball_hand_bonus
        if card.id == Boss_Orders:
            return active_config.search_boss_orders_bonus if plan.target >= 0 else 0
        if card.id == Premium_Power_Pro:
            return active_config.search_premium_power_bonus if plan.attack_index >= 0 else 0

    if option.type == OptionType.ATTACH and card is not None and plan.energy:
        return active_config.search_attach_energy_bonus

    if option.type == OptionType.RETREAT and plan.attacker >= 1:
        return active_config.search_retreat_bonus

    return 0.0


def apply_search_policy(
    select,
    base_scores: list[float],
    context: SelectContext,
    plan: AttackPlan,
    state,
    my_state,
    op_state,
    config: AgentConfig | None = None,
) -> list[float]:
    """Adjust a score list with a lightweight search-inspired bonus for plan-aligned actions."""
    adjusted = list(base_scores)
    for index, score in enumerate(adjusted):
        option = select.option[index]
        bonus = search_action_bonus(
            option=option,
            context=context,
            plan=plan,
            state=state,
            my_state=my_state,
            op_state=op_state,
            card=None,
            config=config,
        )
        adjusted[index] = score + bonus
    return adjusted


def agent(obs_dict: dict) -> list[int]:
    """Main Agent Function.

    Each element in the returned list must be >= 0 and < len(obs.select.option).
    The list length must be between obs.select.minCount and obs.select.maxCount (inclusive), with no duplicate elements.

    Returns:
        list[int]: A list of option index.
    """
    obs = to_observation_class(obs_dict)
    if obs.select == None:
        return my_deck

    state = obs.current
    select = obs.select
    context = select.context
    my_index = state.yourIndex
    my_state = state.players[my_index]
    op_state = state.players[1 - my_index]
    my_prize = len(my_state.prize)

    global plan
    global pre_turn
    global ability_used
    if pre_turn != state.turn:
        pre_turn = state.turn
        plan = AttackPlan()
        ability_used = False

    field_counts = defaultdict(int)
    hand_counts = defaultdict(int)
    discard_counts = defaultdict(int)

    for card in my_state.active + my_state.bench:
        if card == None:
            continue
        field_counts[card.id] += 1

    for card in my_state.hand:
        hand_counts[card.id] += 1

    for card in my_state.discard:
        discard_counts[card.id] += 1

    has_basic_energy_in_hand = any(card_table[c.id].cardType == CardType.BASIC_ENERGY for c in my_state.hand)
    basic_energy_in_discard = sum(1 for c in my_state.discard if card_table[c.id].cardType == CardType.BASIC_ENERGY)

    stadium_id = 0
    for card in state.stadium:
        stadium_id = card.id

    can_attack = False
    if context == SelectContext.MAIN:
        can_switch = False
        can_op_switch = False
        for o in select.option:
            if o.type == OptionType.PLAY:
                card = get_card(obs, AreaType.HAND, o.index, my_index)
                if card.id == Switch:
                    can_switch = True
                elif card.id == Boss_Orders:
                    can_op_switch = True
            elif o.type == OptionType.EVOLVE:
                card = get_card(obs, AreaType.HAND, o.index, my_index)
                if card.id in card_table and not card_table[card.id].basic:
                    can_op_switch = True
            elif o.type == OptionType.RETREAT:
                can_switch = True
            elif o.type == OptionType.ATTACK:
                can_attack = True

        my_cards = [my_state.active[0]]
        for pokemon in my_state.bench:
            my_cards.append(pokemon)
        op_cards = [op_state.active[0]]
        for pokemon in op_state.bench:
            op_cards.append(pokemon)

        if state.turn >= 2:
            best_score = -1
            for i, my_pokemon in enumerate(my_cards):
                if my_pokemon is None:
                    continue
                if i != 0 and not can_switch:
                    break
                
                p_data = card_table[my_pokemon.id]
                moves = []
                if my_pokemon.id in card_db.cards:
                    db_card = card_db.get_card(my_pokemon.id)
                    if hasattr(db_card, "moves") and db_card.moves:
                        moves = [m for m in db_card.moves if not m.name.startswith('[Ability]')]
                
                num_attacks = max(len(moves), len(p_data.attacks)) if p_data.attacks else len(moves)
                if num_attacks == 0:
                    continue

                for a in range(num_attacks):
                    energy_required = 0
                    base_damage = 0
                    base_score = 0
                    
                    if a < len(moves):
                        m = moves[a]
                        energy_required = len(m.cost)
                        base_damage = m.damage or 0
                    elif p_data.attacks:
                        energy_required = a + 1
                        base_damage = 50 * (a + 1)

                    if is_main_attacker(my_pokemon.id):
                        base_score += 10 * min(3, basic_energy_in_discard)

                    if base_damage <= 0:
                        continue

                    more_energy = False
                    energy_count = len(my_pokemon.energies)
                    if i == 0 and can_attack:
                        if p_data.attacks and a < len(p_data.attacks):
                            atk_id = p_data.attacks[a]
                            if not any(o.type == OptionType.ATTACK and o.attackId == atk_id for o in select.option):
                                continue

                    if energy_count < energy_required:
                        if has_basic_energy_in_hand and not state.energyAttached:
                            energy_count += 1
                            if energy_count < energy_required:
                                continue
                            else:
                                more_energy = True
                        else:
                            continue

                    for j, op_pokemon in enumerate(op_cards):
                        if op_pokemon is None:
                            continue
                        if j != 0 and not can_op_switch:
                            break
                        damage = base_damage
                        op_data = card_table[op_pokemon.id]
                        if op_data.weakness is not None and op_data.weakness == p_data.energyType:
                            damage *= 2
                        elif op_data.resistance is not None and op_data.resistance == p_data.energyType:
                            damage = max(0, damage - 30)

                        prize = prize_count(op_pokemon) if op_pokemon.hp <= damage else 0
                        score = estimate_attack_score(
                            base_damage=damage,
                            target_hp=op_pokemon.hp,
                            weakness=op_data.weakness,
                            resistance=op_data.resistance,
                            prize_value=prize,
                            energy_count=energy_count,
                            attacker_energy_type=p_data.energyType,
                            base_score=base_score,
                        )
                        score += pokemon_score(op_pokemon) * 0.01

                        if len(op_state.prize) <= prize:
                            score = 50000

                        if i == 0:
                            score += 220
                        if j == 0:
                            score += 300
                        score += target_priority_score(
                            target_hp=op_pokemon.hp,
                            target_max_hp=card_table[op_pokemon.id].hp,
                            prize_value=prize,
                            is_active=j == 0,
                        )
                        score += energy_count
                        if best_score < score:
                            best_score = score
                            plan.attacker = i
                            plan.target = j
                            plan.attack_index = a
                            plan.remain_hp = op_pokemon.hp - damage
                            plan.energy = more_energy

    def energy_score(pokemon: Pokemon, active: bool) -> int:
        energy_count = len(pokemon.energies)
        score = 8000
        if active:
            score += 10
        p_data = card_table.get(pokemon.id)
        if p_data:
            max_cost = get_pokemon_max_cost(pokemon.id)
            if is_main_attacker(pokemon.id):
                score += 15
                if energy_count < max_cost:
                    score += 100
                else:
                    score -= 30
            elif not p_data.basic:
                if energy_count < max_cost:
                    score += 80
                else:
                    score -= 40
            else:
                p_name = p_data.name
                has_evo = any(c.evolvesFrom == p_name for cid, c in card_table.items() if cid in my_deck and not c.basic)
                if has_evo and energy_count < max_cost:
                    score += 50
                elif energy_count < 1 and max_cost > 0:
                    score += 20
                else:
                    score -= 80
        return score

    scores = []
    for o in select.option:
        score = 0
        if o.type == OptionType.NUMBER:
            score = o.number
        elif o.type == OptionType.YES:
            score = 1
        elif o.type == OptionType.CARD:
            card = get_card(obs, o.area, o.index, o.playerIndex)
            if card != None:
                energy_count = 0
                if isinstance(card, Pokemon):
                    energy_count = len(card.energies)
                if context == SelectContext.SWITCH or context == SelectContext.TO_ACTIVE:
                    if o.playerIndex == my_index:
                        score += energy_count * 2
                        if o.index == plan.attacker - 1:
                            score += 100
                        score += bench_priority_score(
                            pokemon_id=card.id,
                            energy_count=energy_count,
                            bench_count=len(my_state.bench),
                            is_active=False,
                        )
                        p_data = card_table.get(card.id)
                        if p_data:
                            if is_main_attacker(card.id):
                                score += 20
                            elif not p_data.basic and energy_count >= 2:
                                score += 15
                            elif p_data.basic and energy_count >= 2:
                                score += 10
                            else:
                                score += 5
                    else:
                        if o.index == plan.target - 1:
                            score += 100
                elif context == SelectContext.SETUP_ACTIVE_POKEMON:
                    score = setup_priority_score(
                        pokemon_id=card.id,
                        turn=state.turn,
                        has_active_pokemon=bool(my_state.active and my_state.active[0]),
                        bench_count=len(my_state.bench),
                        hand_energy_count=1 if has_basic_energy_in_hand else 0,
                    )
                elif context == SelectContext.TO_HAND:
                    score = 200 - hand_counts[card.id] * 100
                    p_data = card_table.get(card.id)
                    if p_data:
                        if p_data.cardType == CardType.BASIC_ENERGY:
                            if not ability_used or not state.energyAttached:
                                score += 30
                            else:
                                score -= 1
                        elif p_data.cardType == CardType.POKEMON:
                            if not p_data.basic:
                                prev_stage = p_data.evolvesFrom
                                has_prev = any(card_table[cid].name == prev_stage for cid in field_counts if field_counts[cid] > 0)
                                if has_prev:
                                    score += 30
                                else:
                                    score -= 15
                            else:
                                curr_count = field_counts[card.id] + hand_counts[card.id]
                                if curr_count == 0:
                                    score += 50
                                elif curr_count == 1:
                                    score += 10
                                else:
                                    score -= 100
                elif context == SelectContext.ATTACH_FROM:
                    score = energy_score(card, o.area == AreaType.ACTIVE)
        elif o.type == OptionType.PLAY:
            card = get_card(obs, AreaType.HAND, o.index, my_index)
            data = card_table[card.id]
            if data.cardType == CardType.POKEMON:
                score = 20000
                if data.basic:
                    if field_counts[card.id] >= 2 or len(my_state.bench) >= 4:
                        score = -1
            else:
                score = 10000
                if card.id == Switch:
                    if plan.attacker <= 0:
                        score = -1
                    else:
                        score = 6000
                elif card.id == Premium_Power_Pro:
                    if state.supporterPlayed and plan.remain_hp <= 0:
                        score = -1
                    elif not can_attack:
                        if not state.supporterPlayed and hand_counts[Carmine] > 0 and hand_counts[Lillie_Determination] == 0:
                            score = 3050
                        else:
                            score = -1
                    else:
                        score = 5000
                elif card.id == Dusk_Ball:
                    score = draw_priority_score(
                        card_id=card.id,
                        hand_size=len(my_state.hand),
                        bench_count=len(my_state.bench),
                        prize_count=len(op_state.prize),
                        has_active_pokemon=bool(my_state.active and my_state.active[0]),
                    )
                    score += 1000
                elif card.id == Boss_Orders:
                    if plan.target >= 1:
                        score = 3200
                    else:
                        score = -1
                elif card.id == Carmine:
                    score = 3000 + supporter_priority_score(
                        plan_ready=plan.attack_index >= 0 and plan.target >= 0,
                        has_supporter=state.supporterPlayed,
                        hand_supporters=hand_counts[Carmine] + hand_counts[Lillie_Determination],
                        prize_count=len(op_state.prize),
                    )
                elif card.id == Lillie_Determination:
                    score = 3100 + supporter_priority_score(
                        plan_ready=plan.attack_index >= 0 and plan.target >= 0,
                        has_supporter=state.supporterPlayed,
                        hand_supporters=hand_counts[Carmine] + hand_counts[Lillie_Determination],
                        prize_count=len(op_state.prize),
                    )
                elif card.id == Gravity_Mountain:
                    if stadium_id == 0:
                        score = -1
                elif card.id == Mega_Signal:
                    score = 3500
                elif card.id == Wondrous_Patch:
                    score = 3600
        elif o.type == OptionType.ATTACH:
            card = get_card(obs, AreaType.HAND, o.index, my_index)
            pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)
            if card.id == Hero_Cape:
                score = 7000
                if pokemon is not None:
                    if is_main_attacker(pokemon.id):
                        score += 200
                    else:
                        score += 100
            else:
                if pokemon is not None:
                    score = energy_score(pokemon, o.inPlayArea == AreaType.ACTIVE)
                    if o.inPlayArea == AreaType.ACTIVE:
                        if plan.attacker == 0 and plan.energy:
                            score += 200
                    else:
                        if plan.attacker == 1 + o.inPlayIndex and plan.energy:
                            score += 200
        elif o.type == OptionType.EVOLVE:
            pokemon = get_card(obs, o.inPlayArea, o.inPlayIndex, my_index)
            score = 9000 + (len(pokemon.energies) if pokemon is not None else 0)
        elif o.type == OptionType.ABILITY:
            card = get_card(obs, o.area, o.index, my_index)
            if card is not None and card.id == 1267:  # Lumiose City
                score = 1
            else:
                score = 30000
        elif o.type == OptionType.RETREAT:
            if my_state.active and my_state.active[0] is not None:
                active = my_state.active[0]
                damage_ratio = retreat_priority_score(
                    active_hp=active.hp,
                    max_hp=card_table[active.id].hp,
                    bench_count=len(my_state.bench),
                    prize_count=len(op_state.prize),
                )
                if plan.attacker >= 1 or damage_ratio >= 40:
                    score = 2000 + damage_ratio
                else:
                    score = -1
            else:
                score = -1
        elif o.type == OptionType.ATTACK:
            score = 1000
            if my_state.active and my_state.active[0] is not None:
                active_card = my_state.active[0]
                p_data = card_table.get(active_card.id)
                if p_data and p_data.attacks and o.attackId in p_data.attacks:
                    atk_idx = p_data.attacks.index(o.attackId)
                    if plan.attack_index == atk_idx:
                        score += 100

        score += search_action_bonus(
            option=o,
            context=context,
            plan=plan,
            state=state,
            my_state=my_state,
            op_state=op_state,
            card=get_card(obs, AreaType.HAND, o.index, my_index) if o.type in {OptionType.PLAY, OptionType.ATTACH} else None,
        )
        scores.append(score)

    if context == SelectContext.MAIN:
        scores = apply_search_policy(
            select=select,
            base_scores=scores,
            context=context,
            plan=plan,
            state=state,
            my_state=my_state,
            op_state=op_state,
            config=AGENT_CONFIG,
        )

    desc_indices = [i for i, _ in sorted(enumerate(scores), key=lambda x: x[1], reverse=True)]
    if context == SelectContext.MAIN:
        o = select.option[desc_indices[0]]
        if o.type == OptionType.ABILITY:
            ability_used = True
    return desc_indices[:select.maxCount]
