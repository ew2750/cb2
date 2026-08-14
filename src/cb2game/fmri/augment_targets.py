"""Deterministically add validated target/instruction pairs to one run set."""

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from cb2game.fmri.utils import (
    ID_TO_ASSET,
    LANDMARK_NAME_TO_TEXT,
    create_instructions,
    get_distance,
)
from cb2game.server.card_enums import Color, Shape


def _card_signature(prop):
    card = prop["card_init"]
    return (int(card["color"]), int(card["shape"]), int(card["count"]))


def _offset(coord):
    return (2 * int(coord["r"]) + int(coord["a"]), int(coord["c"]))


def _card_description(prop):
    card = prop["card_init"]
    return (
        f"{int(card['count'])} {Color(int(card['color'])).name.lower()} "
        f"{Shape(int(card['shape'])).name.lower()}"
    )


def _landmark_description(tile):
    return LANDMARK_NAME_TO_TEXT[ID_TO_ASSET[int(tile["asset_id"])]].replace(
        "a ", "", 1
    ).replace("an ", "", 1)


def _choose_landmarks(target, assets, count=2):
    target_coord = target["prop_info"]["location"]

    def ranked(origin, candidates):
        return sorted(
            candidates,
            key=lambda tile: (
                get_distance(origin, tile["cell"]["coord"]),
                _landmark_description(tile),
                _offset(tile["cell"]["coord"]),
                int(tile["asset_id"]),
            ),
        )

    first = ranked(target_coord, assets)[0]
    selected = [first]
    origin = first["cell"]["coord"]
    while len(selected) < count:
        remaining = [tile for tile in assets if tile not in selected]
        used_descriptions = {_landmark_description(tile) for tile in selected}
        distinct = [
            tile for tile in remaining
            if _landmark_description(tile) not in used_descriptions
        ]
        next_tile = ranked(origin, distinct or remaining)[0]
        selected.append(next_tile)
        origin = next_tile["cell"]["coord"]

    chain = []
    origin = target_coord
    for tile in selected:
        distance = int(get_distance(origin, tile["cell"]["coord"]))
        chain.append([copy.deepcopy(tile), distance])
        origin = tile["cell"]["coord"]
    return chain


def augment(runset_dir, target_count, report_path):
    runset_dir = Path(runset_dir).resolve()
    runset_name = runset_dir.name.replace("runset_", "")
    paths = sorted(runset_dir.glob("scenario_0001_t*_l*.json"))
    if len(paths) != 8:
        raise RuntimeError(f"Expected eight scenario-001 variants, found {len(paths)}")
    scenarios = {path: json.loads(path.read_text(encoding="utf-8")) for path in paths}
    base_path = runset_dir / "scenario_0001_t0_l0.json"
    base = scenarios[base_path]

    cards = {
        int(prop["id"]): prop
        for prop in base["prop_update"]["props"]
        if prop.get("card_init") is not None
    }
    existing_groups = [tuple(int(x) for x in group) for group in base["target_card_ids"]]
    if any(len(group) != 1 for group in existing_groups):
        raise RuntimeError("Target augmentation requires one card per target group")
    existing_ids = [group[0] for group in existing_groups]
    if len(existing_ids) >= target_count:
        print(f"Already has {len(existing_ids)} targets; no changes needed")
        return

    # All variants must describe the same card layout and existing target order.
    base_card_signature = tuple(
        sorted((card_id, _card_signature(prop), _offset(prop["prop_info"]["location"]))
               for card_id, prop in cards.items())
    )
    for path, scenario in scenarios.items():
        variant_cards = {
            int(prop["id"]): prop
            for prop in scenario["prop_update"]["props"]
            if prop.get("card_init") is not None
        }
        variant_signature = tuple(
            sorted((card_id, _card_signature(prop), _offset(prop["prop_info"]["location"]))
                   for card_id, prop in variant_cards.items())
        )
        variant_groups = [tuple(int(x) for x in group)
                          for group in scenario["target_card_ids"]]
        if variant_signature != base_card_signature or variant_groups != existing_groups:
            raise RuntimeError(f"Condition layout mismatch in {path}")

    signature_counts = Counter(_card_signature(prop) for prop in cards.values())
    candidates = [
        prop for card_id, prop in cards.items()
        if card_id not in existing_ids
        and signature_counts[_card_signature(prop)] == 1
    ]
    needed = target_count - len(existing_ids)
    if len(candidates) < needed:
        raise RuntimeError(
            f"Need {needed} visually unique candidates, found {len(candidates)}"
        )

    assets = [
        tile for tile in base["map"]["tiles"]
        if ID_TO_ASSET[int(tile["asset_id"])] in LANDMARK_NAME_TO_TEXT
    ]
    if len(assets) < 2:
        raise RuntimeError("At least two usable landmarks are required")

    # Greedy farthest-point selection spreads targets over the map. Ties prefer
    # a card closer to a landmark, then the lower stable card ID.
    selected_locations = [cards[target_id]["prop_info"]["location"]
                          for target_id in existing_ids]
    selected = []
    while len(selected) < needed:
        def score(prop):
            location = prop["prop_info"]["location"]
            separation = min(get_distance(location, other)
                             for other in selected_locations)
            nearest_landmark = min(
                get_distance(location, tile["cell"]["coord"]) for tile in assets
            )
            return (separation, -nearest_landmark, -int(prop["id"]))

        choice = max(candidates, key=score)
        candidates.remove(choice)
        selected.append(choice)
        selected_locations.append(choice["prop_info"]["location"])

    new_ids = [int(prop["id"]) for prop in selected]
    new_landmarks = {
        target_id: _choose_landmarks(cards[target_id], assets)
        for target_id in new_ids
    }
    generation_scenario = {
        "map": base["map"],
        "prop_update": base["prop_update"],
        "target_card_ids": [[target_id] for target_id in new_ids],
        "landmarks": new_landmarks,
    }
    # Resetting the seed ensures easy/hard versions make identical lexical
    # choices; only the intended syntactic construction changes.
    instruction_seed = int.from_bytes(
        hashlib.sha256(
            f"cb2-target-augmentation:{runset_name}".encode("utf-8")
        ).digest()[:4],
        "big",
    )
    np.random.seed(instruction_seed)
    easy_instructions = create_instructions(generation_scenario, hard=False)
    np.random.seed(instruction_seed)
    hard_instructions = create_instructions(generation_scenario, hard=True)

    for path, scenario in scenarios.items():
        linguistic_level = int(path.stem.rsplit("_l", 1)[1])
        texts = hard_instructions if linguistic_level else easy_instructions
        scenario["target_card_ids"].extend([[target_id] for target_id in new_ids])
        for target_id in new_ids:
            scenario.setdefault("landmarks", {})[str(target_id)] = copy.deepcopy(
                new_landmarks[target_id]
            )
        scenario["objectives"].extend(
            {
                "sender": 2,
                "text": text,
                "uuid": "",
                "completed": False,
                "cancelled": False,
            }
            for text in texts
        )
        path.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")

    report = [
        f"# Run set {runset_name} target augmentation audit",
        "",
        f"Targets increased from {len(existing_ids)} to {target_count} without "
        "changing the 12x12 map or any card appearance.",
        "",
        "Every added target has a color-shape-count signature that occurs only "
        f"once among the {len(cards)} retained cards. Two nearby non-pink "
        "landmarks were "
        "assigned to each target, and matched easy/hard instructions were "
        "generated with identical lexical choices.",
        "",
        "| Card ID | Card | Cell | Landmark chain |",
        "|---:|---|---|---|",
    ]
    for target_id in new_ids:
        prop = cards[target_id]
        chain = "; ".join(
            f"{_landmark_description(tile)} at distance {distance}"
            for tile, distance in new_landmarks[target_id]
        )
        report.append(
            f"| {target_id} | {_card_description(prop)} | "
            f"{_offset(prop['prop_info']['location'])} | {chain} |"
        )
    report.extend(["", "## Generated instructions", ""])
    for target_id, easy, hard in zip(new_ids, easy_instructions, hard_instructions):
        report.extend([
            f"### Card {target_id}",
            "",
            f"- Easy: {easy}",
            f"- Hard: {hard}",
            "",
        ])
    Path(report_path).resolve().write_text(
        "\n".join(report).rstrip() + "\n", encoding="utf-8"
    )
    print(f"Added target IDs: {new_ids}")
    print(f"Updated {len(paths)} condition files to {target_count} targets")
    print(f"Audit report: {Path(report_path).resolve()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runset_dir")
    parser.add_argument("--target-count", type=int, default=18)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    augment(args.runset_dir, args.target_count, args.report)


if __name__ == "__main__":
    main()
