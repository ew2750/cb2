"""Scanner-ready, local-only CerealBar task runner.

The Unity WebGL client remains open for the full run. A local controller loads
all four 2x2 conditions into that same session, eliminating per-block Unity
startup screens and browser reloads.
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import random
import re
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import pygame

from cb2game.fmri.main import (
    Display,
    HOST,
    LOBBY,
    MATERIALS_DIR,
    PREDEFINED_FORWARD_CONDITION_LABELS,
    grab_pygame_focus,
    restore_unity_focus_after_rating,
    validate_scenario_files,
)
from cb2game.fmri.utils import (
    browser_window_geometry,
    display_layout,
    open_browser,
)
from cb2game.pyclient.game_endpoint import Action
from cb2game.pyclient.remote_client import RemoteClient
from cb2game.server.hex import HecsCoord, HexBoundary


logger = logging.getLogger(__name__)
TASK_SECONDS = 30.0
FIXATION_SECONDS = 10.0
RUN_ONSET_FIXATION_SECONDS = 20.0
RUN_OFFSET_FIXATION_SECONDS = 20.0
MAP_SIZE = 12
PINK_CARD_COLOR = 5
PINK_HOUSE_ASSET_ID = 22
PATH_TILE_ASSET_ID = 28
GAME_POLL_INTERVAL_NS = 50_000_000
EVENT_COLUMNS = ("onset", "duration", "trial_type")
SPAWNABLE_TILE_ASSET_IDS = {0, 3, PATH_TILE_ASSET_ID}


def _safe_label(value):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(value)).strip("-") or "unknown"


class EventFile:
    """Incremental BIDS-compatible event writer using scanner-trigger time zero."""

    def __init__(self, output_dir, subject_id, run_number):
        output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"sub-{_safe_label(subject_id)}_task-cerealbar_"
            f"run-{int(run_number):02d}_events.tsv"
        )
        self.path = output_dir / filename
        repeat = 2
        while self.path.exists():
            self.path = output_dir / filename.replace(
                "_events.tsv", f"_repeat-{repeat:02d}_events.tsv"
            )
            repeat += 1
        self._handle = self.path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(
            self._handle, fieldnames=EVENT_COLUMNS, delimiter="\t"
        )
        self._writer.writeheader()
        self._handle.flush()

    def append(self, onset, duration, trial_type):
        self._writer.writerow(
            {
                "onset": f"{onset:.6f}",
                "duration": f"{duration:.6f}",
                "trial_type": trial_type,
            }
        )
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def close(self):
        if not self._handle.closed:
            self._handle.close()


def _condition_paths(materials_dir, run_set, hard_environment, hard_language,
                     template_number, scenario_id):
    condition_lookup = {
        "HH": (hard_environment, hard_language),
        "EH": (0, hard_language),
        "HE": (hard_environment, 0),
        "EE": (0, 0),
    }
    template_index = (int(template_number) - 1) % len(
        PREDEFINED_FORWARD_CONDITION_LABELS
    )
    labels = PREDEFINED_FORWARD_CONDITION_LABELS[template_index]
    required = list(condition_lookup.values())
    directory_ok, errors, available = validate_scenario_files(
        str(materials_dir), run_set, required
    )
    if not directory_ok:
        raise FileNotFoundError(f"Cannot read materials for {run_set}: {errors}")

    missing = [condition for condition in required if not available.get(condition)]
    if missing:
        raise FileNotFoundError(f"Missing 2x2 condition materials: {missing}")

    shared_ids = set.intersection(
        *(
            {entry["scenario_id"] for entry in available[condition]}
            for condition in required
        )
    )
    if not shared_ids:
        raise FileNotFoundError("No scenario ID is shared by all four conditions")
    selected_id = min(shared_ids) if scenario_id is None else int(scenario_id)
    if selected_id not in shared_ids:
        raise FileNotFoundError(
            f"Scenario {selected_id} is not available in all four conditions"
        )

    forward = []
    for label in labels:
        condition = condition_lookup[label]
        entry = next(
            item
            for item in available[condition]
            if item["scenario_id"] == selected_id
        )
        forward.append((label, condition, Path(entry["full_path"])))
    # A/B/C/D denote HH/EH/HE/EE. Each run uses one cyclic forward order and
    # then its mirror: run 1 = A B C D D C B A, run 2 = B C D A A D C B, etc.
    return forward + list(reversed(forward))


def _inside_runtime_map(location):
    """Return whether a serialized HECS coordinate fits the runtime map.

    Scenario coordinates use HECS ``(a, r, c)`` coordinates, whereas Unity's
    map dimensions are offset-grid rows and columns.  A HECS coordinate's
    offset row is ``2 * r + a``; comparing ``r`` directly with ``rows`` leaves
    out-of-range cells in a cropped map and crashes the WebGL client while it
    populates its tile array.
    """
    if location is None:
        return False
    offset_row = 2 * int(location.get("r", -1)) + int(location.get("a", -1))
    offset_col = int(location.get("c", -1))
    return (
        0 <= offset_row < MAP_SIZE
        and 0 <= offset_col < MAP_SIZE
    )


def _prepare_runtime_materials(scenario, path):
    """Apply scanner presentation constraints to one static scenario."""
    map_data = scenario.get("map", {})
    map_data["rows"] = MAP_SIZE
    map_data["cols"] = MAP_SIZE
    cropped_tiles = []
    for tile in map_data.get("tiles", []):
        location = tile.get("cell", {}).get("coord")
        if not _inside_runtime_map(location):
            continue
        if tile.get("asset_id") == PINK_HOUSE_ASSET_ID:
            tile["asset_id"] = PATH_TILE_ASSET_ID
        cropped_tiles.append(tile)
    map_data["tiles"] = cropped_tiles

    props = []
    for prop in scenario.get("prop_update", {}).get("props", []):
        card = prop.get("card_init")
        location = prop.get("prop_info", {}).get("location")
        if not _inside_runtime_map(location):
            continue
        if card is not None and card.get("color") == PINK_CARD_COLOR:
            continue
        if card is not None:
            card["selected"] = 0
        props.append(prop)
    scenario.setdefault("prop_update", {})["props"] = props
    valid_prop_ids = {prop.get("id") for prop in props}

    landmarks = scenario.get("landmarks", {})
    retained_trials = []
    for objective, target_group in zip(
        scenario.get("objectives", []), scenario.get("target_card_ids", [])
    ):
        text = objective.get("text", "")
        text = re.sub(r"\bstreetlights\b", "lampposts", text, flags=re.IGNORECASE)
        text = re.sub(r"\bstreetlight\b", "lamppost", text, flags=re.IGNORECASE)
        objective["text"] = text
        target_ids = [int(target_id) for target_id in target_group]
        target_landmarks = []
        for target_id in target_ids:
            target_landmarks.extend(
                landmarks.get(str(target_id), landmarks.get(target_id, []))
            )
        landmarks_are_valid = all(
            landmark[0].get("asset_id") != PINK_HOUSE_ASSET_ID
            and _inside_runtime_map(
                landmark[0].get("cell", {}).get("coord")
            )
            for landmark in target_landmarks
        )
        if (
            all(target_id in valid_prop_ids for target_id in target_ids)
            and landmarks_are_valid
            and "pink house" not in text.lower()
        ):
            retained_trials.append((objective, target_group))

    if not retained_trials:
        raise ValueError(f"No eligible non-pink targets remain in {path}")
    scenario["objectives"] = [trial[0] for trial in retained_trials]
    scenario["target_card_ids"] = [trial[1] for trial in retained_trials]
    retained_target_ids = {
        int(target_id)
        for _, target_group in retained_trials
        for target_id in target_group
    }
    scenario["landmarks"] = {
        str(target_id): landmarks.get(str(target_id), landmarks.get(target_id, []))
        for target_id in retained_target_ids
    }
    return scenario


def _randomize_player_spawn(scenario, path, subject_id, run_number,
                            block_index):
    """Place the playable actor on a reproducibly random reachable cell."""
    tiles = scenario.get("map", {}).get("tiles", [])
    tiles_by_coord = {
        (
            int(tile["cell"]["coord"]["a"]),
            int(tile["cell"]["coord"]["r"]),
            int(tile["cell"]["coord"]["c"]),
        ): tile
        for tile in tiles
    }
    if not tiles_by_coord:
        raise ValueError(f"No map tiles available for randomized spawn in {path}")

    def neighbors(coord_key):
        coord = HecsCoord(*coord_key)
        tile = tiles_by_coord[coord_key]
        boundary = HexBoundary(int(tile["cell"]["boundary"]["edges"]))
        for neighbor in coord.neighbors():
            neighbor_key = (neighbor.a, neighbor.r, neighbor.c)
            neighbor_tile = tiles_by_coord.get(neighbor_key)
            if neighbor_tile is None:
                continue
            neighbor_boundary = HexBoundary(
                int(neighbor_tile["cell"]["boundary"]["edges"])
            )
            if boundary.get_edge_between(coord, neighbor):
                continue
            if neighbor_boundary.get_edge_between(neighbor, coord):
                continue
            yield neighbor_key

    # Identify the largest mutually reachable part of the map so a random
    # start cannot land in an isolated pocket behind map boundaries.
    unseen = set(tiles_by_coord)
    components = []
    while unseen:
        start = min(unseen)
        component = set()
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            unseen.discard(current)
            queue.extend(neighbor for neighbor in neighbors(current)
                         if neighbor not in component)
        components.append(component)
    largest_component = max(components, key=lambda component: (len(component), -min(component)[1]))

    occupied = {
        (
            int(prop["prop_info"]["location"]["a"]),
            int(prop["prop_info"]["location"]["r"]),
            int(prop["prop_info"]["location"]["c"]),
        )
        for prop in scenario.get("prop_update", {}).get("props", [])
        if prop.get("prop_info", {}).get("location") is not None
    }
    actors = scenario.get("actor_state", {}).get("actors", [])
    playable_actors = [
        actor for actor in actors if int(actor.get("actor_role", -1)) == 1
    ]
    if len(playable_actors) != 1:
        raise ValueError(
            f"Expected one playable role-1 actor in {path}, found "
            f"{len(playable_actors)}"
        )
    for actor in actors:
        if actor is playable_actors[0]:
            continue
        location = actor.get("location")
        if location is not None:
            occupied.add(
                (int(location.get("a", -1)), int(location.get("r", -1)),
                 int(location.get("c", -1)))
            )

    candidates = sorted(
        coord_key for coord_key in largest_component
        if coord_key not in occupied
        and int(tiles_by_coord[coord_key].get("asset_id", -1))
        in SPAWNABLE_TILE_ASSET_IDS
        and sum(1 for _ in neighbors(coord_key)) >= 2
    )
    if len(candidates) < 8:
        raise ValueError(
            f"Only {len(candidates)} safe randomized spawn cells remain in {path}"
        )

    scenario_stem = re.sub(r"_t\d+_l\d+$", "", Path(path).stem)
    material_key = f"{Path(path).parent.name}/{scenario_stem}"
    seed_text = f"{subject_id}:{run_number}:{material_key}:spawn"
    spawn_seed = int.from_bytes(
        hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big"
    )
    rng = random.Random(spawn_seed)
    rng.shuffle(candidates)
    spawn = candidates[int(block_index) % len(candidates)]
    headings = [0, 60, 120, 180, 240, 300]
    heading_rng = random.Random(f"{spawn_seed}:{block_index}:heading")
    heading = heading_rng.choice(headings)

    playable_actors[0]["location"] = {
        "a": spawn[0], "r": spawn[1], "c": spawn[2]
    }
    playable_actors[0]["rotation_degrees"] = float(heading)
    scenario.setdefault("kvals", {})["fmri_spawn"] = {
        "block_index": int(block_index),
        "coord": {"a": spawn[0], "r": spawn[1], "c": spawn[2]},
        "offset_row": 2 * spawn[1] + spawn[0],
        "offset_col": spawn[2],
        "rotation_degrees": heading,
        "seed": spawn_seed,
    }
    logger.info(
        "Randomized block %s spawn to HECS=%s offset=(%s,%s) heading=%s",
        block_index + 1, spawn, 2 * spawn[1] + spawn[0], spawn[2], heading,
    )


def _load_scenario(path, subject_id, run_number, block_index=0,
                   trial_offset=None):
    with Path(path).open(encoding="utf-8") as handle:
        scenario = json.load(handle)
    scenario = _prepare_runtime_materials(scenario, path)
    scenario.setdefault("subject", {}).update(
        {"subject_id": str(subject_id), "run": int(run_number)}
    )
    scenario["kvals"] = scenario.get("kvals") or {}
    scenario["kvals"]["fmri_auto_advance_instructions"] = True
    _randomize_player_spawn(
        scenario, path, subject_id, run_number, block_index
    )

    objectives = scenario.get("objectives", [])
    target_groups = scenario.get("target_card_ids", [])
    if len(objectives) != len(target_groups):
        raise ValueError(
            f"Instruction/target count mismatch in {path}: "
            f"{len(objectives)} instructions, {len(target_groups)} targets"
        )
    paired_trials = list(zip(objectives, target_groups))
    scenario_stem = re.sub(
        r"_t\d+_l\d+$", "", Path(path).stem
    )
    material_key = f"{Path(path).parent.name}/{scenario_stem}"
    seed_text = f"{subject_id}:{run_number}:{material_key}"
    shuffle_seed = int.from_bytes(
        hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big"
    )
    random.Random(shuffle_seed).shuffle(paired_trials)
    # Every block starts from the next target in one shared shuffled sequence.
    # ``trial_offset`` is advanced by the number completed in the prior block
    # plus one, which discards the unfinished target that was active when the
    # block ended. Because language variants share target IDs, their rephrased
    # instructions remain attached to the correct cards after this rotation.
    if paired_trials:
        if trial_offset is None:
            trial_offset = block_index
        rotation = int(trial_offset) % len(paired_trials)
        paired_trials = paired_trials[rotation:] + paired_trials[:rotation]
    if paired_trials:
        shuffled_objectives, shuffled_targets = zip(*paired_trials)
        scenario["objectives"] = list(shuffled_objectives)
        scenario["target_card_ids"] = list(shuffled_targets)
    scenario["kvals"]["fmri_instruction_order"] = [
        list(group) for group in scenario.get("target_card_ids", [])
    ]
    logger.info(
        "Shuffled instruction order for %s with seed %s: %s",
        Path(path).name, shuffle_seed,
        scenario["kvals"]["fmri_instruction_order"],
    )

    for index, objective in enumerate(scenario.get("objectives", [])):
        # The supplied materials use empty objective UUIDs. Unique UUIDs are
        # required for reliable completion and activation of the next item.
        if not objective.get("uuid"):
            objective["uuid"] = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"cb2-fmri:{Path(path).resolve()}:{subject_id}:{run_number}:"
                f"{block_index}:{index}",
            ))
    scenario["duration_s"] = 3600
    return json.dumps(scenario)


def _install_runtime_keymap(browser, pilot_wasd=False):
    """Support the bundled WebGL build as well as rebuilt Unity clients."""
    pilot_entries = """
            mapping['w'] = ['ArrowUp', 'ArrowUp', 38];
            mapping['s'] = ['ArrowDown', 'ArrowDown', 40];
            mapping['a'] = ['ArrowLeft', 'ArrowLeft', 37];
            mapping['d'] = ['ArrowRight', 'ArrowRight', 39];
    """ if pilot_wasd else ""
    browser.execute_script(
        r"""
        if (!window.cb2ScannerKeymapInstalled) {
          window.cb2ScannerKeymapInstalled = true;
          const mapping = {
            '2': ['ArrowUp', 'ArrowUp', 38],
            '3': ['ArrowDown', 'ArrowDown', 40],
            '4': ['ArrowLeft', 'ArrowLeft', 37],
            '5': ['ArrowRight', 'ArrowRight', 39],
            '6': ['s', 'KeyS', 83]
          };
          __PILOT_ENTRIES__
          for (const type of ['keydown', 'keyup']) {
            document.addEventListener(type, function(event) {
              const mapped = mapping[event.key.toLowerCase()];
              if (!mapped || event.cb2Mapped) return;
              event.preventDefault();
              event.stopImmediatePropagation();
              const replacement = new KeyboardEvent(type, {
                key: mapped[0], code: mapped[1], keyCode: mapped[2],
                which: mapped[2], bubbles: true, cancelable: true
              });
              Object.defineProperty(replacement, 'cb2Mapped', {value: true});
              (document.querySelector('canvas') || document).dispatchEvent(replacement);
            }, true);
          }
        }
        """.replace("__PILOT_ENTRIES__", pilot_entries)
    )


def _zoom_out_browser_interface(browser):
    """Set Chrome to 67% page zoom for a wider effective game view."""
    try:
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.keys import Keys

        before = browser.execute_script(
            "return [window.innerWidth, window.innerHeight];"
        )
        ActionChains(browser).key_down(Keys.COMMAND).send_keys("-").send_keys(
            "-"
        ).send_keys("-").key_up(Keys.COMMAND).perform()
        time.sleep(0.2)
        after = browser.execute_script(
            "return [window.innerWidth, window.innerHeight];"
        )
        logger.info("Applied 67%% interface zoom: viewport %s -> %s", before, after)
    except Exception as error:
        logger.warning("Could not apply browser interface zoom: %s", error)


def _connect_controller(host, lobby):
    client = RemoteClient(url=host, render=False, lobby_name=lobby)
    connected, reason = client.Connect()
    if not connected:
        raise RuntimeError(f"Could not connect local controller: {reason}")
    game = None
    while game is None:
        game, reason = client.AttachToScenario(scenario_id="")
        if game is None:
            time.sleep(0.05)
    return client, game


def _wait_until(deadline_ns, game=None, fallback_state=None):
    """Wait for an absolute monotonic deadline without network I/O.

    ``GameEndpoint.step`` can block for up to 60 seconds while waiting for a
    state-machine tick.  A quiet participant produces no tick, so game polling
    must never be part of an fMRI timing loop.
    """
    latest_state = fallback_state
    next_game_poll_ns = time.perf_counter_ns()
    while time.perf_counter_ns() < deadline_ns:
        now_ns = time.perf_counter_ns()
        if game is not None and now_ns >= next_game_poll_ns:
            latest_state = _snapshot_game(game, latest_state)
            next_game_poll_ns = now_ns + GAME_POLL_INTERVAL_NS
        pygame.event.pump()
        remaining = (deadline_ns - time.perf_counter_ns()) / 1_000_000_000
        if remaining > 0.002:
            time.sleep(min(0.002, remaining / 2))
    return latest_state


def _snapshot_game(game, fallback_state=None):
    """Consume already-buffered updates without waiting for a future tick."""
    try:
        game._process_pending_messages()  # pylint: disable=protected-access
        for message in game.queued_messages:
            game.socket.send_message(message)
        game.queued_messages = []
        return game._state()  # pylint: disable=protected-access
    except Exception as error:
        logger.warning("Could not refresh game snapshot: %s", error)
        return fallback_state


def _run_task_epoch(game, run_zero_ns, condition_code, event_file,
                    fallback_state=None, deadline_ns=None):
    onset_ns = time.perf_counter_ns()
    if deadline_ns is None:
        deadline_ns = onset_ns + int(TASK_SECONDS * 1_000_000_000)
    latest_state = _wait_until(
        deadline_ns, game=game, fallback_state=fallback_state
    )
    # Capture any completion already buffered at the exact block boundary so a
    # correct selection in the final polling interval is included in the score.
    latest_state = _snapshot_game(game, latest_state)
    offset_ns = time.perf_counter_ns()
    onset = (onset_ns - run_zero_ns) / 1_000_000_000
    duration = (offset_ns - onset_ns) / 1_000_000_000
    event_file.append(onset, duration, condition_code)
    logger.info(
        "Logged %s onset=%.6f duration=%.6f", condition_code, onset, duration
    )
    return latest_state


def _completed_instruction_count(game_state):
    if game_state is None:
        return 0
    return sum(
        1 for instruction in game_state.instructions
        if instruction.completed and not instruction.cancelled
    )


def _has_unfinished_instruction(game_state):
    if game_state is None:
        return False
    return any(
        not instruction.completed and not instruction.cancelled
        for instruction in game_state.instructions
    )


def _trial_type(condition):
    environment, language = condition
    environment_name = "fog" if environment > 0 else "clear"
    language_name = "hard" if language > 0 else "easy"
    return f"language-{language_name}_environment-{environment_name}"


def _send_scenario_load(game, scenario_data):
    """Queue a scenario change without waiting for a network tick."""
    _snapshot_game(game)
    message, reason = Action.LoadScenario(scenario_data).message_to_server(
        game.player_actor
    )
    if message is None:
        raise RuntimeError(f"Could not create scenario-load message: {reason}")
    game.socket.send_message(message)


def _show_fixation(display, game, fallback_state=None, scenario_data=None,
                   duration_s=FIXATION_SECONDS, deadline_ns=None):
    display.show_cross()
    grab_pygame_focus()
    start_ns = time.perf_counter_ns()
    if deadline_ns is None:
        deadline_ns = start_ns + int(duration_s * 1_000_000_000)
    logger.info("Fixation started; planned duration is %.3f seconds", duration_s)
    if scenario_data is not None:
        _send_scenario_load(game, scenario_data)
        logger.info("Queued next condition while fixation remains visible")
        # Loading a new Unity scenario can cause the browser to repaint or
        # reclaim focus on macOS. Raise and redraw the fixation immediately.
        display.show_cross()
        grab_pygame_focus()
    latest_state = _wait_until(
        deadline_ns, game=game, fallback_state=fallback_state
    )
    duration = (time.perf_counter_ns() - start_ns) / 1_000_000_000
    logger.info("Fixation finished after %.6f seconds", duration)
    return latest_state


def run_scanner_task(subject_id, run_number, run_set, hard_environment,
                     hard_language, materials_dir=MATERIALS_DIR,
                     output_dir="data/events", template_number=None,
                     scenario_id=None, host=HOST, lobby=LOBBY,
                     browser_name="firefox", not_in_scanner=False,
                     pilot_wasd=False, display_number=1, window_layout=1):
    run_set = run_set if str(run_set).startswith("runset_") else f"runset_{run_set}"
    template_number = template_number or ((int(run_number) - 1) % 4 + 1)
    schedule = _condition_paths(
        materials_dir, run_set, int(hard_environment), int(bool(hard_language)),
        template_number, scenario_id,
    )

    pygame.init()
    displays = display_layout()
    display_index = int(display_number) - 1
    if display_index < 0 or display_index >= len(displays):
        raise ValueError(
            f"Display {display_number} is unavailable; found {len(displays)} display(s)"
        )
    selected_display = displays[display_index]
    logger.info("Using display %s: %s", display_number, selected_display)
    display = Display(
        background_color="black", foreground_color="white",
        display_index=display_index,
    )
    display.show()
    display.clear()
    display.draw_text("Waiting for scanner — trigger: 5")

    browser_size, browser_position = browser_window_geometry(
        selected_display, window_layout
    )
    logger.info(
        "Using window layout %s: size=%s position=%s",
        window_layout, browser_size, browser_position,
    )
    browser = open_browser(
        fullscreen=False, browser_name=browser_name,
        window_size=browser_size, window_position=browser_position,
    )
    browser.get(f"{host}/play?lobby_name={lobby}&auto=join_game_queue")
    _zoom_out_browser_interface(browser)
    client = None
    events = None
    try:
        client, game = _connect_controller(host, lobby)
        _install_runtime_keymap(browser, pilot_wasd=pilot_wasd)

        trial_offset = 0
        first_label, _, first_path = schedule[0]
        game_state = game.step(
            Action.LoadScenario(
                _load_scenario(
                    first_path, subject_id, run_number, block_index=0,
                    trial_offset=trial_offset,
                )
            )
        )
        logger.info("Preloaded first condition %s behind scanner screen", first_label)

        # Chrome necessarily comes to the front while Unity loads. Recreate the
        # pygame fullscreen window afterwards so the waiting screen, rather
        # than the game, remains visible until the scanner trigger.
        display.hide()
        display.show()
        display.clear()
        display.draw_text("Waiting for scanner — trigger: 5")
        grab_pygame_focus()

        # perf_counter_ns is captured immediately after the trigger event and is
        # the sole run timebase used for event onsets.
        display.await_trigger(in_scanner=not not_in_scanner)
        run_zero_ns = time.perf_counter_ns()
        trigger_utc = datetime.now(timezone.utc).isoformat()
        events = EventFile(output_dir, subject_id, run_number)
        logger.info("Scanner trigger received at %s; events=%s", trigger_utc, events.path)

        scheduled_seconds = RUN_ONSET_FIXATION_SECONDS
        game_state = _show_fixation(
            display, game, fallback_state=game_state,
            duration_s=RUN_ONSET_FIXATION_SECONDS,
            deadline_ns=(
                run_zero_ns
                + int(RUN_ONSET_FIXATION_SECONDS * 1_000_000_000)
            ),
        )

        total_cards_found = 0
        block_scores = []
        for block_index, (label, condition, path) in enumerate(schedule):
            code = _trial_type(condition)
            display.hide()
            restore_unity_focus_after_rating(browser)
            scheduled_seconds += TASK_SECONDS
            game_state = _run_task_epoch(
                game, run_zero_ns, code, events, fallback_state=game_state,
                deadline_ns=(
                    run_zero_ns + int(scheduled_seconds * 1_000_000_000)
                ),
            )
            block_score = _completed_instruction_count(game_state)
            block_scores.append(block_score)
            total_cards_found += block_score
            # The completed instructions have already advanced past their
            # targets. Advance once more to discard the unfinished card that
            # was active at the exact block boundary. If every available item
            # was completed, there is no active card to discard.
            discarded_card = int(_has_unfinished_instruction(game_state))
            trial_offset += block_score + discarded_card
            logger.info(
                "Block %s/%s (%s) complete: %s card(s), run total=%s; "
                "discarded active card=%s; next trial offset=%s",
                block_index + 1, len(schedule), label, block_score,
                total_cards_found, bool(discarded_card), trial_offset,
            )

            if block_index + 1 < len(schedule):
                _, _, next_path = schedule[block_index + 1]
                next_scenario_data = _load_scenario(
                    next_path, subject_id, run_number,
                    block_index=block_index + 1,
                    trial_offset=trial_offset,
                )
                scheduled_seconds += FIXATION_SECONDS
                game_state = _show_fixation(
                    display, game, fallback_state=game_state,
                    scenario_data=next_scenario_data,
                    deadline_ns=(
                        run_zero_ns + int(scheduled_seconds * 1_000_000_000)
                    ),
                )
            else:
                scheduled_seconds += RUN_OFFSET_FIXATION_SECONDS
                game_state = _show_fixation(
                    display, game, fallback_state=game_state,
                    duration_s=RUN_OFFSET_FIXATION_SECONDS,
                    deadline_ns=(
                        run_zero_ns + int(scheduled_seconds * 1_000_000_000)
                    ),
                )

        logger.info(
            "Run complete after %.1f scheduled seconds; block scores=%s; total=%s",
            scheduled_seconds, block_scores, total_cards_found,
        )
        print(f"Run complete. Cards found: {total_cards_found}", flush=True)
        display.show()
        display.clear()
        display.draw_text(f"Run complete. Cards found: {total_cards_found}")
        time.sleep(2)
        return events.path
    finally:
        if events is not None:
            events.close()
        if client is not None:
            client.Reset()
        browser.quit()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Run the local CerealBar fMRI task")
    parser.add_argument("subject_id")
    parser.add_argument("run_number", type=int)
    parser.add_argument("run_set")
    parser.add_argument("hard_environment", type=int, help="Hard fog value (normally 3)")
    parser.add_argument("hard_language", type=int, help="1 for hard language")
    parser.add_argument("--materials-dir", default=MATERIALS_DIR)
    parser.add_argument("--output-dir", default="data/events")
    parser.add_argument("--condition-template", type=int, choices=range(1, 5))
    parser.add_argument("--scenario-id", type=int)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--lobby", default=LOBBY)
    parser.add_argument("--browser", choices=("firefox", "chrome"), default="firefox")
    parser.add_argument("--not-in-scanner", action="store_true")
    parser.add_argument(
        "--pilot-wasd", action="store_true",
        help="Also enable W/S/A/D movement for pilot testing",
    )
    parser.add_argument(
        "--display-number", type=int, default=1,
        help="1-based monitor number (1 is the primary display)",
    )
    parser.add_argument(
        "--window-layout", type=int, choices=(1, 2, 3), default=1,
        help="1=max non-fullscreen, 2=upper two-thirds, 3=centered half-size",
    )
    args = parser.parse_args()
    run_scanner_task(
        args.subject_id, args.run_number, args.run_set,
        args.hard_environment, args.hard_language,
        materials_dir=args.materials_dir, output_dir=args.output_dir,
        template_number=args.condition_template, scenario_id=args.scenario_id,
        host=args.host, lobby=args.lobby, browser_name=args.browser,
        not_in_scanner=args.not_in_scanner, pilot_wasd=args.pilot_wasd,
        display_number=args.display_number,
        window_layout=args.window_layout,
    )


if __name__ == "__main__":
    main()
