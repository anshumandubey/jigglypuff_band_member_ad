import json
import argparse

from cg.game import (
    battle_start,
    battle_select,
    battle_finish,
    visualize_data,
)

from main import agent
from tools.inspect_observation import inspect_observation


def load_deck():
    with open("deck.csv") as f:
        return [int(line.strip()) for line in f if line.strip()]


def save_visualizations(obs_log, action_log):
    # replay.html
    html = visualize_data()
    with open("replay.html", "w", encoding="utf-8") as f:
        f.write(html)

    # vis.json
    vis = json.loads(html)

    for i in range(len(vis)):
        vis[i]["obs"] = obs_log[i]
        vis[i]["action"] = [action_log[i], action_log[i]]

    with open("vis.json", "w", encoding="utf-8") as f:
        json.dump(vis, f)

    print("Saved replay.html")
    print("Saved vis.json")


def print_winner(result):
    print("\n" + "=" * 70)

    if result == 0:
        print("Winner: Player 0")
    elif result == 1:
        print("Winner: Player 1")
    else:
        print("Result code:", result)

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true", help="Print readable observations.")
    parser.add_argument("--inspect-options", type=int, default=12)
    args = parser.parse_args()

    deck = load_deck()

    obs_dict, start_data = battle_start(deck, deck)

    if obs_dict is None:
        print("Failed to start battle.")
        print(start_data)
        return

    obs_log = [""]
    action_log = [None]

    step = 0

    try:
        while True:

            result = obs_dict["current"]["result"]

            if result != -1:
                print_winner(result)
                break

            select = obs_dict["select"]

            print(
                f"[Step {step:03d}] "
                f"Context={select['context']} "
                f"Options={len(select['option'])}"
            )
            if args.inspect:
                print(inspect_observation(obs_dict, max_options=args.inspect_options))

            action = agent(obs_dict)

            print("Action:", action)

            # Save observation (remove binary search data)
            obs_copy = dict(obs_dict)
            obs_copy.pop("search_begin_input", None)

            obs_log.append(obs_copy)
            action_log.append(action)

            obs_dict = battle_select(action)

            step += 1

    finally:
        save_visualizations(obs_log, action_log)
        battle_finish()


if __name__ == "__main__":
    main()
