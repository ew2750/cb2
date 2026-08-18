import copy
import hashlib
import logging
import json
import os
import argparse
import shutil
from pathlib import Path

import numpy as np
from cb2game.pyclient.remote_client import RemoteClient
from cb2game.fmri.utils import (
    ASSET_TO_ID,
    ID_TO_ASSET,
    LANDMARK_NAME_TO_TEXT,
    MAX_SCENARIO_DURATION,
    N_LANDMARKS,
    get_distance,
    open_browser,
    set_difficulty,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

HZ = 10
HOST = 'http://localhost:8080'
LOBBY = 'open'
MAX_CARDS = None
N_TARGETS = 15
N_DISTRACTORS = 2
CARD_COVERS = True
N_SETS = 10
N_RUNS_PER_SET = 8
CONDITION_ORDER_FILENAME = "condition_order.txt"
DEFAULT_CONDITION_ORDER_DIR = Path(__file__).resolve().parent / "materials"
CONDITION_VARIANTS = {
    "env_easy_lang_easy": (0, 0),
    "env_easy_lang_hard": (0, 1),
    "env_hard_lang_easy": (2, 0),
    "env_hard_lang_hard": (2, 1),
}
EXPECTED_ENVIRONMENT_LEVELS = {0, 2}
PINK_CARD_COLOR_ID = 5
PINK_HOUSE_ASSET_ID = ASSET_TO_ID["GROUND_TILE_HOUSE_PINK"]
PATH_TILE_ASSET_ID = ASSET_TO_ID["GROUND_TILE_PATH"]
MAX_UNIQUE_LANDSCAPE_ATTEMPTS = 50


def validate_condition_variants():
    """Keep output restricted to clear t0 and hard-fog t2 variants."""
    environment_levels = {
        environment for environment, _ in CONDITION_VARIANTS.values()
    }
    if environment_levels != EXPECTED_ENVIRONMENT_LEVELS:
        raise ValueError(
            "Scanner materials must use exactly environment levels t0 and t2; "
            f"found {sorted(environment_levels)}"
        )

def validate_condition_order_file(set_path):
    """Validate eight run-specific, material-owned counterbalance orders."""
    path = Path(set_path) / CONDITION_ORDER_FILENAME
    if not path.is_file():
        raise FileNotFoundError(
            f"Create {path} before sampling; it must contain run1 through "
            "run8 condition orders"
        )
    orders = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        if not content:
            continue
        label, separator, sequence = content.partition(":")
        if not separator:
            raise ValueError(
                f"{path} must use lines such as "
                "'run1: D A B C C B A D'"
            )
        run_label = label.strip().lower().replace("-", "_")
        if run_label in orders:
            raise ValueError(f"Duplicate {run_label} entry in {path}")
        tokens = sequence.upper().replace(",", " ").split()
        if (len(tokens) != 8 or tokens[0] != "D"
                or any(token not in "ABCD" for token in tokens)
                or any(tokens.count(token) != 2 for token in "ABCD")
                or tokens != list(reversed(tokens))):
            raise ValueError(
                f"Invalid order for {run_label} in {path}: {tokens}; expected "
                "a D-first palindrome containing each A/B/C/D twice"
            )
        orders[run_label] = tuple(tokens)
    expected_runs = {f"run{run_number}" for run_number in range(1, 9)}
    if set(orders) != expected_runs:
        raise ValueError(
            f"{path} must define exactly run1 through run8; found "
            f"{sorted(orders)}"
        )
    order_values = list(orders.values())
    counts = sorted(order_values.count(order) for order in set(order_values))
    if len(set(order_values)) != 6 or counts != [1, 1, 1, 1, 2, 2]:
        raise ValueError(
            f"{path} must use all six unique D-first palindromes plus two "
            "single repeats"
        )


def ensure_condition_order_file(
        set_path, set_number,
        condition_order_dir=DEFAULT_CONDITION_ORDER_DIR):
    """Seed a new output set from the material-owned order templates."""
    destination = Path(set_path) / CONDITION_ORDER_FILENAME
    requested_source = (
        Path(condition_order_dir)
        / f"set{set_number}"
        / CONDITION_ORDER_FILENAME
    )
    bundled_source = (
        DEFAULT_CONDITION_ORDER_DIR
        / f"set{set_number}"
        / CONDITION_ORDER_FILENAME
    )
    destination_is_legacy = destination.is_file() and not any(
        line.split("#", 1)[0].strip().lower().startswith("run1:")
        for line in destination.read_text(encoding="utf-8").splitlines()
    )
    if not destination.is_file() or destination_is_legacy:
        source = next(
            (
                candidate for candidate in (requested_source, bundled_source)
                if candidate.is_file()
                and candidate.resolve() != destination.resolve()
            ),
            None,
        )
        if source is None:
            raise FileNotFoundError(
                f"Missing condition-order template for set{set_number}; "
                f"checked {requested_source} and {bundled_source}"
            )
        shutil.copyfile(source, destination)
        logger.info("Copied condition order %s -> %s", source, destination)
    validate_condition_order_file(set_path)


def remove_pink_components(scenario):
    """Remove pink cards and replace pink-house tiles with ordinary paths."""
    props = scenario.get("prop_update", {}).get("props", [])
    scenario["prop_update"]["props"] = [
        prop for prop in props
        if (prop.get("card_init") or {}).get("color") != PINK_CARD_COLOR_ID
    ]
    for tile in scenario.get("map", {}).get("tiles", []):
        if tile.get("asset_id") == PINK_HOUSE_ASSET_ID:
            tile["asset_id"] = PATH_TILE_ASSET_ID
    return scenario


def validate_no_pink_components(scenario):
    """Fail generation rather than writing a material that contains pink."""
    pink_cards = [
        prop.get("id")
        for prop in scenario.get("prop_update", {}).get("props", [])
        if (prop.get("card_init") or {}).get("color") == PINK_CARD_COLOR_ID
    ]
    pink_tiles = [
        tile.get("cell", {}).get("coord")
        for tile in scenario.get("map", {}).get("tiles", [])
        if tile.get("asset_id") == PINK_HOUSE_ASSET_ID
    ]
    pink_instructions = [
        objective.get("text", "")
        for objective in scenario.get("objectives", [])
        if "pink" in objective.get("text", "").lower()
    ]
    if pink_cards or pink_tiles or pink_instructions:
        raise ValueError(
            "Pink content remained after filtering: "
            f"cards={pink_cards}, tiles={pink_tiles}, "
            f"instructions={pink_instructions}"
        )


def landscape_signature(scenario):
    """Return a stable signature for enforcing one unique map per run."""
    map_data = scenario.get("map", {})
    payload = {
        "rows": map_data.get("rows"),
        "cols": map_data.get("cols"),
        "tiles": map_data.get("tiles", []),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def clean_scenario(scenario, card_covers=CARD_COVERS):
    scenario['scenario_id'] = 'scenario'
    scenario['prop_update'] = dict(props=scenario['props'])
    scenario['map'] = scenario['map_update']
    scenario['actor_state'] = dict(actors=scenario['actors'])
    del scenario['props']
    del scenario['map_update']
    del scenario['instructions']
    del scenario['live_feedback']
    del scenario['actors']

    scenario['actor_state']['population'] = 2
    scenario['actor_state']['player_id'] = 21
    scenario['actor_state']['player_role'] = 2

    scenario['turn_state']['turn'] = 1
    scenario['turn_state']['moves_remaining'] = 1000000
    scenario['turn_state']['turns_left'] = 0

    objectives = [dict(
        sender=2,
        text='',
        uuid='',
        completed=False,
        cancelled=False
    )]

    scenario['objectives'] = objectives

    for card in scenario['prop_update']['props']:
        if card_covers:
            card['card_init']['hidden'] = False
        else:
            card['card_init']['hidden'] = True

    for actor in scenario['actor_state']['actors']:
        if actor['actor_role'] == 2:
            actor['location'] = dict(
                a=100,
                r=100,
                c=100
            )
        elif actor['actor_role'] == 1:
            actor['asset_id'] = 2

    scenario['duration_s'] = MAX_SCENARIO_DURATION

    return scenario


def sample_scenario(
        browser,
        host=HOST,
        lobby=LOBBY
):
    suffix = "&auto=join_game_queue"
    url = f"{host}/play?lobby_name={lobby}"
    browser.get(url + suffix)
    logger.info(f"Trying to connect to {host} and lobby {lobby}")
    client = RemoteClient(url=host, render=False, lobby_name=lobby)
    game = None
    try:
        connected, reason = client.Connect()
        if not connected:
            raise ConnectionError(f"Could not connect to sampler lobby: {reason}")
        logger.info("Client connected")

        game, reason = client.JoinGame()
        if game is None:
            raise ConnectionError(f"Could not join sampler game: {reason}")
        logger.info("Attached scenario")
        scenario = game._state().to_dict()
    finally:
        if game is not None:
            game.close()
        client.Reset()

    scenario = clean_scenario(scenario)
    scenario = resample_scenario(scenario)

    return scenario


def sample_card_properties():
    return dict(
        # Pink cards are excluded because their appearance is easily confused
        # with the pink house landmark in the scanner display.
        color=int(np.random.choice([1, 2, 3, 4, 6])),
        shape=np.random.randint(1, 7),
        count=np.random.randint(1, 3),
        selected=0,
        hidden=False
    )


def sample_landmarks(n_landmarks, target_card, assets, available_cards, temp=1):
    target_loc = target_card['prop_info']['location']
    landmarks = []
    excluded_distractor_card_ids = set()

    assets_used = []
    assets_by_description = {}
    for asset in assets:
        asset_description = LANDMARK_NAME_TO_TEXT[ID_TO_ASSET[asset['asset_id']]]
        if asset_description not in assets_by_description:
            assets_by_description[asset_description] = []
        assets_by_description[asset_description].append(asset)

    for i in range(n_landmarks):
        _assets = [
            dict(asset=x, d=get_distance(x['cell']['coord'], target_loc)) for x in assets if x not in assets_used
        ]
        _assets = sorted(_assets, key=lambda x: x['d'], reverse=False)
        probs = 1 / np.exp(np.arange(len(_assets)) ** (1 / temp))
        probs /= probs.sum()
        s = np.random.choice(_assets, p=probs)
        landmark, distance = s['asset'], s['d']
        landmarks.append((landmark, distance))
        assets_used.append(landmark)
        if i == 0:  # Find and exclude any other cards that happen to match the sequence of landmark descriptions
            for card_id in available_cards:
                reference_loc = available_cards[card_id]['prop_info']['location']
                match = False
                for landmark, d in landmarks:
                    asset_description = LANDMARK_NAME_TO_TEXT[ID_TO_ASSET[landmark['asset_id']]]
                    candidates = assets_by_description[asset_description]
                    match = False
                    for candidate in candidates:
                        _d = get_distance(reference_loc, candidate['cell']['coord'])
                        if d == _d:
                            match = True
                            break
                    if not match:
                        break
                    reference_loc = landmark['cell']['coord']
                if match:
                    excluded_distractor_card_ids.add(card_id)

        target_loc = landmark['cell']['coord']

    return landmarks, excluded_distractor_card_ids


def resample_scenario(
        scenario,
        n_targets=N_TARGETS,
        n_distractors=N_DISTRACTORS,
        n_landmarks=N_LANDMARKS,
        max_cards=MAX_CARDS
):
    remove_pink_components(scenario)
    cards = scenario['prop_update']['props']
    assets = []
    for asset in scenario['map']['tiles']:
        asset_id = asset['asset_id']
        asset_name = ID_TO_ASSET[asset_id]
        if asset_name in LANDMARK_NAME_TO_TEXT:
            assets.append(asset)

    if max_cards and len(cards) > max_cards:
        cards = np.random.choice(cards, size=max_cards, replace=False)
    cards = list(cards)

    scenario['prop_update']['props'] = list(cards)

    _cards = cards[1:]  # For some reason selection borders are buggy when card 0 is a target, so exclude
    if len(_cards) < n_targets:
        raise ValueError(
            f"Not enough non-pink cards for {n_targets} targets: "
            f"only {len(_cards)} eligible cards"
        )
    target_set = np.random.choice(_cards, size=n_targets, replace=False)
    targets = {card['id']: card for card in target_set}
    target_ids = [int(x) for x in np.random.permutation(list(targets.keys()))]
    target_properties = {}
    available_cards = {x['id']: x for x in cards if x['id'] not in target_ids}

    landmarks = {}
    excluded_distractor_card_ids = {}
    for target_id in target_ids:
        target_card = targets[target_id]
        _target_properties = sample_card_properties()
        target_properties[target_id] = _target_properties
        landmarks[target_id], excluded_distractor_card_ids[target_id] = sample_landmarks(
            n_landmarks,
            target_card,
            assets,
            available_cards
        )
        for card in cards:  # Give the target card its assigned properties
            if card['id'] == target_id:
                card['card_init'] = _target_properties
            else:  # No other card can have the target's properties (for now)
                if card['card_init'] == _target_properties:
                    nontarget_properties = _target_properties
                    while nontarget_properties in target_properties.values():
                        nontarget_properties = sample_card_properties()
                    card['card_init'] = nontarget_properties

    for target_id in target_ids:
        _target_properties = target_properties[target_id]
        _available_ids = list(set(list(available_cards.keys())) - excluded_distractor_card_ids[target_id])
        if len(_available_ids) < n_distractors:
            raise ValueError(
                f"Not enough eligible distractors for target {target_id}: "
                f"needed {n_distractors}, found {len(_available_ids)}"
            )
        distractor_ids = np.random.choice(_available_ids, size=n_distractors, replace=False)
        distractor_ids = list(distractor_ids)
        for distractor_id in distractor_ids:
            distractor = available_cards.pop(distractor_id)
            distractor['card_init'] = _target_properties

    scenario['target_card_ids'] = [[x] for x in target_ids]
    scenario['landmarks'] = landmarks

    return scenario


def sample_set(
        set_number,
        browser,
        n_runs=N_RUNS_PER_SET,
        host=HOST,
        lobby=LOBBY,
        outdir='scenarios_sampled',
        condition_order_dir=DEFAULT_CONDITION_ORDER_DIR,
        overwrite=False,
        seen_landscapes=None,
):
    validate_condition_variants()
    if int(set_number) < 1 or int(set_number) > N_SETS:
        raise ValueError(f"Set number must be 1-{N_SETS}: {set_number}")
    if seen_landscapes is None:
        seen_landscapes = set()

    set_path = Path(outdir) / f"set{set_number}"
    set_path.mkdir(parents=True, exist_ok=True)
    ensure_condition_order_file(
        set_path, set_number, condition_order_dir=condition_order_dir
    )

    for run_number in range(1, n_runs + 1):
        logger.info("Sampling set%s, run%s", set_number, run_number)
        expected_paths = [
            set_path / f"run{run_number}_{variant_name}.json"
            for variant_name in CONDITION_VARIANTS
        ]
        if not overwrite and all(path.exists() for path in expected_paths):
            with expected_paths[0].open(encoding="utf-8") as handle:
                seen_landscapes.add(landscape_signature(json.load(handle)))
            logger.info("All four files exist; skipping set%s/run%s", set_number, run_number)
            continue

        scenario = None
        for attempt in range(1, MAX_UNIQUE_LANDSCAPE_ATTEMPTS + 1):
            try:
                candidate = sample_scenario(browser, host=host, lobby=lobby)
            except ValueError as error:
                logger.warning(
                    "Rejected set%s/run%s attempt %s: %s",
                    set_number, run_number, attempt, error,
                )
                continue
            signature = landscape_signature(candidate)
            if signature in seen_landscapes:
                logger.warning(
                    "Rejected duplicate landscape for set%s/run%s attempt %s",
                    set_number, run_number, attempt,
                )
                continue
            seen_landscapes.add(signature)
            scenario = candidate
            break
        if scenario is None:
            raise RuntimeError(
                f"Could not sample a valid unique landscape for "
                f"set{set_number}/run{run_number} after "
                f"{MAX_UNIQUE_LANDSCAPE_ATTEMPTS} attempts"
            )

        for variant_name, (environment, language) in CONDITION_VARIANTS.items():
            variant = set_difficulty(
                copy.deepcopy(scenario),
                task_difficulty=environment,
                linguistic_complexity=language,
            )
            variant["scenario_id"] = f"run{run_number}"
            validate_no_pink_components(variant)
            path = set_path / f"run{run_number}_{variant_name}.json"
            with path.open("w", encoding="utf-8") as handle:
                json.dump(variant, handle, indent=2)


def main(
        browser,
        n_sets=N_SETS,
        n_runs=N_RUNS_PER_SET,
        host=HOST,
        lobby=LOBBY,
        outdir=Path(__file__).resolve().parent / "materials",
        condition_order_dir=DEFAULT_CONDITION_ORDER_DIR,
        overwrite=False
):
    if n_sets != N_SETS or n_runs != N_RUNS_PER_SET:
        logger.warning(
            "Requested %s sets x %s runs; the scanner design expects %s x %s",
            n_sets, n_runs, N_SETS, N_RUNS_PER_SET,
        )
    seen_landscapes = set()
    for set_number in range(1, n_sets + 1):
        sample_set(
            set_number,
            browser,
            n_runs=n_runs,
            host=host,
            lobby=lobby,
            outdir=outdir,
            condition_order_dir=condition_order_dir,
            overwrite=overwrite,
            seen_landscapes=seen_landscapes,
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser("fmri")
    parser.add_argument("--host", type=str, default=HOST)
    parser.add_argument("--lobby", type=str, default=LOBBY)
    parser.add_argument(
        "--outdir", type=str,
        default=str(Path(__file__).resolve().parent / "materials"),
    )
    parser.add_argument(
        "--condition-orders-dir", type=str,
        default=str(DEFAULT_CONDITION_ORDER_DIR),
        help="Directory containing setN/condition_order.txt templates",
    )
    parser.add_argument("--sets", type=int, default=N_SETS)
    parser.add_argument("--runs", type=int, default=N_RUNS_PER_SET)
    parser.add_argument("--overwrite", action='store_true')
    args = parser.parse_args()

    host = args.host
    lobby = args.lobby

    browser = open_browser(fullscreen=False)

    excp = None
    try:
        main(
            browser, n_sets=args.sets, n_runs=args.runs,
            host=host, lobby=lobby, outdir=args.outdir,
            condition_order_dir=args.condition_orders_dir,
            overwrite=args.overwrite,
        )
    except Exception as e:
        excp = e

    browser.close()

    if excp is not None:
        raise excp
