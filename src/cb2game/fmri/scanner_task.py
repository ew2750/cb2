"""Scanner-ready, local-only CerealBar task runner.

The Unity WebGL client remains open for the full run. A local controller loads
all four 2x2 conditions into that same session, eliminating per-block Unity
startup screens and browser reloads.
"""

import argparse
import csv
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pygame

from cb2game.fmri.main import (
    Display,
    HOST,
    LOBBY,
    MATERIALS_DIR,
    grab_pygame_focus,
    restore_unity_focus_after_rating,
)
from cb2game.fmri.utils import (
    browser_window_geometry,
    display_layout,
    open_browser,
)
from cb2game.pyclient.game_endpoint import Action
from cb2game.pyclient.remote_client import RemoteClient


logger = logging.getLogger(__name__)
TIMING_PROFILES = {
    "fmri": {
        "task": 30.0,
        "fixation": 10.0,
        "onset_fixation": 20.0,
        "offset_fixation": 20.0,
    },
    "practice": {
        "task": 30.0,
        "fixation": 3.0,
        "onset_fixation": 3.0,
        "offset_fixation": 3.0,
    },
    "dry-run": {
        "task": 3.0,
        "fixation": 1.0,
        "onset_fixation": 2.0,
        "offset_fixation": 2.0,
    },
}
# The fMRI profile is the single source for actual-task durations. These
# aliases support fallback timing and practice-screen explanatory text.
TASK_SECONDS = TIMING_PROFILES["fmri"]["task"]
FIXATION_SECONDS = TIMING_PROFILES["fmri"]["fixation"]
RUN_ONSET_FIXATION_SECONDS = TIMING_PROFILES["fmri"]["onset_fixation"]
RUN_OFFSET_FIXATION_SECONDS = TIMING_PROFILES["fmri"]["offset_fixation"]
GAME_POLL_INTERVAL_NS = 50_000_000
EVENT_COLUMNS = ("onset", "duration", "trial_type")
CONDITION_ORDER_FILENAME = "condition_order.txt"
CONDITION_FILES = {
    "A": ((2, 1), "env_hard_lang_hard"),
    "B": ((0, 1), "env_easy_lang_hard"),
    "C": ((2, 0), "env_hard_lang_easy"),
    "D": ((0, 0), "env_easy_lang_easy"),
}
N_MATERIAL_SETS = 10
N_RUNS_PER_SET = 8
MATERIAL_VARIANT_SUFFIX_RE = (
    r"_(?:env_(?:easy|hard)_lang_(?:easy|hard)|t\d+_l\d+)$"
)


def _safe_label(value):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(value)).strip("-") or "unknown"


def _material_label(value):
    """Format numbered materials while also supporting the practice labels."""
    try:
        return f"{int(value):02d}"
    except (TypeError, ValueError):
        return _safe_label(value)


class EventFile:
    """Incremental BIDS-compatible event writer using scanner-trigger time zero."""

    def __init__(self, output_dir, subject_id, session_id,
                 set_number, run_number):
        output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"sub-{_safe_label(subject_id)}_ses-{_safe_label(session_id)}_"
            f"task-cerealbar_set-{_material_label(set_number)}_"
            f"run-{_material_label(run_number)}_events.tsv"
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
        self._writer.writerow({
            "onset": f"{onset:.6f}",
            "duration": f"{duration:.6f}",
            "trial_type": trial_type,
        })
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def close(self):
        if not self._handle.closed:
            self._handle.close()


def _numbered_value(value, prefix, minimum, maximum):
    text = str(value).strip().lower()
    if text.startswith(prefix):
        text = text[len(prefix):]
    try:
        number = int(text)
    except ValueError as error:
        raise ValueError(
            f"{prefix} must be a number from {minimum} to {maximum}: {value!r}"
        ) from error
    if number < minimum or number > maximum:
        raise ValueError(
            f"{prefix} must be from {minimum} to {maximum}: {number}"
        )
    return number


def _validate_condition_sequence(path, run_label, tokens):
    if (len(tokens) != 8
            or any(token not in CONDITION_FILES for token in tokens)
            or any(tokens.count(token) != 2 for token in CONDITION_FILES)):
        raise ValueError(
            f"{path} {run_label} must contain exactly eight condition codes "
            f"with each of A/B/C/D appearing twice; found {tokens}"
        )
    if tokens[0] != "D":
        raise ValueError(
            f"{path} {run_label} must start with D "
            f"(env_easy_lang_easy); found {tokens[0]}"
        )
    if tokens != list(reversed(tokens)):
        raise ValueError(
            f"{path} {run_label} must be palindromic; found {tokens}"
        )


def _read_condition_order(set_path, run_label):
    path = Path(set_path) / CONDITION_ORDER_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"Missing condition order file: {path}")
    orders = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        if not content:
            continue
        label, separator, sequence = content.partition(":")
        if not separator:
            raise ValueError(
                f"{path} must use run-specific lines such as "
                "'run1: D A B C C B A D'"
            )
        normalized_label = label.strip().lower().replace("-", "_")
        tokens = sequence.upper().replace(",", " ").split()
        if normalized_label in orders:
            raise ValueError(f"Duplicate {normalized_label} entry in {path}")
        _validate_condition_sequence(path, normalized_label, tokens)
        orders[normalized_label] = tuple(tokens)
    normalized_run = str(run_label).strip().lower().replace("-", "_")
    if normalized_run not in orders:
        raise ValueError(
            f"{path} has no condition order for {normalized_run}; "
            f"available entries are {sorted(orders)}"
        )
    return orders[normalized_run]


def _condition_paths(materials_dir, set_number, run_number):
    materials_path = Path(materials_dir).expanduser().resolve()
    practice_aliases = {"prac", "practice", "set_prac", "run_prac"}
    if (str(set_number).strip().lower() in practice_aliases
            or str(run_number).strip().lower() in practice_aliases):
        set_number = "prac"
        run_number = "prac"
        set_path = materials_path / "set_prac"
        run_stem = "run_prac"
    else:
        set_number = _numbered_value(set_number, "set", 1, N_MATERIAL_SETS)
        run_number = _numbered_value(run_number, "run", 1, N_RUNS_PER_SET)
        set_path = materials_path / f"set{set_number}"
        run_stem = f"run{run_number}"
    labels = _read_condition_order(set_path, run_stem)

    condition_paths = {}
    missing = []
    for label, (condition, variant_name) in CONDITION_FILES.items():
        path = set_path / f"{run_stem}_{variant_name}.json"
        condition_paths[label] = (condition, path)
        if not path.is_file():
            missing.append(path)
    if missing:
        formatted = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(
            f"Missing condition materials for set{set_number}/run{run_number}:\n"
            f"{formatted}"
        )
    return [
        (label, condition_paths[label][0], condition_paths[label][1])
        for label in labels
    ]


def _serialized_location(location):
    """Return a normalized HECS location without assuming any map size."""
    if not isinstance(location, dict):
        return None
    try:
        return {key: int(location[key]) for key in ("a", "r", "c")}
    except (KeyError, TypeError, ValueError):
        return None


def _player_pose_from_state(game_state):
    """Extract the playable actor's pose at a task-block boundary."""
    if game_state is None:
        return None
    state = game_state.to_dict()
    actors = state.get("actors", [])
    actor = next(
        (item for item in actors if int(item.get("actor_role", -1)) == 1),
        None,
    )
    if actor is None:
        logger.warning("Could not carry player pose: role-1 actor is missing")
        return None
    location = _serialized_location(actor.get("location"))
    if location is None:
        logger.warning(
            "Could not carry player pose: invalid map location %s", location
        )
        return None
    return {
        "location": {
            "a": location["a"],
            "r": location["r"],
            "c": location["c"],
        },
        "rotation_degrees": float(actor.get("rotation_degrees", 0.0)),
    }


def _apply_player_pose(scenario, player_pose, path):
    """Apply the preceding block's player pose to the next condition."""
    if player_pose is None:
        return
    playable_actors = [
        actor
        for actor in scenario.get("actor_state", {}).get("actors", [])
        if int(actor.get("actor_role", -1)) == 1
    ]
    if len(playable_actors) != 1:
        raise ValueError(
            f"Expected one playable role-1 actor in {path}, found "
            f"{len(playable_actors)}"
        )
    material_cells = {
        tuple(normalized[key] for key in ("a", "r", "c"))
        for tile in scenario.get("map", {}).get("tiles", [])
        for normalized in [_serialized_location(tile.get("cell", {}).get("coord"))]
        if normalized is not None
    }
    pose_cell = tuple(player_pose["location"][key] for key in ("a", "r", "c"))
    if pose_cell not in material_cells:
        logger.warning(
            "Could not carry player pose into %s: location %s is absent from "
            "the material map; using the material's actor start",
            Path(path).name, player_pose["location"],
        )
        return
    playable_actors[0]["location"] = dict(player_pose["location"])
    playable_actors[0]["rotation_degrees"] = float(
        player_pose["rotation_degrees"]
    )
    scenario.setdefault("kvals", {})["fmri_pose_carryover"] = {
        "location": dict(player_pose["location"]),
        "rotation_degrees": float(player_pose["rotation_degrees"]),
    }
    logger.info(
        "Carried player pose into %s: location=%s heading=%s",
        Path(path).name, player_pose["location"], player_pose["rotation_degrees"],
    )


def _load_scenario(path, subject_id, session_id, block_index=0,
                   trial_offset=None, player_pose=None):
    with Path(path).open(encoding="utf-8") as handle:
        scenario = json.load(handle)
    scenario.setdefault("subject", {}).update({
        "subject_id": str(subject_id),
        "session_id": str(session_id),
    })
    scenario["kvals"] = scenario.get("kvals") or {}
    scenario["kvals"]["fmri_session_id"] = str(session_id)
    scenario["kvals"]["fmri_material_set"] = Path(path).parent.name
    scenario["kvals"]["fmri_material_run"] = re.sub(
        MATERIAL_VARIANT_SUFFIX_RE, "", Path(path).stem
    )
    scenario["kvals"]["fmri_auto_advance_instructions"] = True
    _apply_player_pose(scenario, player_pose, path)

    objectives = scenario.get("objectives", [])
    target_groups = scenario.get("target_card_ids", [])
    if len(objectives) != len(target_groups):
        raise ValueError(
            f"Instruction/target count mismatch in {path}: "
            f"{len(objectives)} instructions, {len(target_groups)} targets"
        )
    # Preserve material order. Rotation only advances past items completed in
    # the preceding block and the unfinished item discarded at its boundary.
    if objectives:
        if trial_offset is None:
            trial_offset = block_index
        rotation = int(trial_offset) % len(objectives)
        scenario["objectives"] = objectives[rotation:] + objectives[:rotation]
        scenario["target_card_ids"] = (
            target_groups[rotation:] + target_groups[:rotation]
        )
    scenario["kvals"]["fmri_instruction_order"] = [
        list(group) for group in scenario.get("target_card_ids", [])
    ]
    logger.info(
        "Material instruction order for %s: %s", Path(path).name,
        scenario["kvals"]["fmri_instruction_order"],
    )

    for index, objective in enumerate(scenario.get("objectives", [])):
        if not objective.get("uuid"):
            objective["uuid"] = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"cb2-fmri:{Path(path).resolve()}:{subject_id}:"
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


def _draw_fixation(display, instruction_lines=None):
    """Draw a normal cross or centered practice-mode rest instructions."""
    if not instruction_lines:
        display.show_cross()
        return
    display.show()
    display.clear()
    rendered = [
        display.font.render(line, True, pygame.Color(display.foreground_color))
        for line in instruction_lines
    ]
    line_gap = max(12, display.font.get_linesize() // 2)
    total_height = sum(surface.get_height() for surface in rendered)
    total_height += line_gap * (len(rendered) - 1)
    y = (display.H - total_height) // 2
    for surface in rendered:
        rect = surface.get_rect(
            center=(display.W // 2, y + surface.get_height() // 2)
        )
        display.screen.blit(surface, rect)
        y += surface.get_height() + line_gap
    pygame.display.flip()


def _practice_fixation_text(actual_seconds):
    return (
        "In the actual fMRI task, you will now look at a +",
        f"for {int(actual_seconds)} seconds.",
        "Rest your brain and keep still.",
    )


def _show_fixation(display, game, fallback_state=None, scenario_data=None,
                   duration_s=FIXATION_SECONDS, deadline_ns=None,
                   instruction_lines=None):
    _draw_fixation(display, instruction_lines)
    grab_pygame_focus()
    start_ns = time.perf_counter_ns()
    if deadline_ns is None:
        deadline_ns = start_ns + int(duration_s * 1_000_000_000)
    logger.info("Fixation started; planned duration is %.3f seconds", duration_s)
    if scenario_data is not None:
        _send_scenario_load(game, scenario_data)
        logger.info("Queued next condition while fixation remains visible")
        _draw_fixation(display, instruction_lines)
        grab_pygame_focus()
    latest_state = _wait_until(
        deadline_ns, game=game, fallback_state=fallback_state
    )
    duration = (time.perf_counter_ns() - start_ns) / 1_000_000_000
    logger.info("Fixation finished after %.6f seconds", duration)
    return latest_state


def run_scanner_task(subject_id, session_id, set_number, run_number,
                     materials_dir=MATERIALS_DIR,
                     output_dir="data/events", host=HOST, lobby=LOBBY,
                     browser_name="firefox", not_in_scanner=False,
                     timing_mode="fmri", pilot_wasd=False,
                     display_number=1, window_layout=1):
    if not str(session_id).strip():
        raise ValueError("sessionID cannot be blank")
    if timing_mode not in TIMING_PROFILES:
        raise ValueError(
            f"Timing mode must be one of {tuple(TIMING_PROFILES)}, "
            f"received {timing_mode!r}"
        )
    timing = TIMING_PROFILES[timing_mode]
    task_seconds = timing["task"]
    fixation_seconds = timing["fixation"]
    onset_fixation_seconds = timing["onset_fixation"]
    offset_fixation_seconds = timing["offset_fixation"]
    practice_mode = timing_mode == "practice"
    logger.info("Using %s timing profile: %s", timing_mode, timing)

    if timing_mode in ("practice", "dry-run"):
        set_number = "prac"
        run_number = "prac"
        pilot_wasd = True
    else:
        set_number = _numbered_value(set_number, "set", 1, N_MATERIAL_SETS)
        run_number = _numbered_value(run_number, "run", 1, N_RUNS_PER_SET)
    schedule = _condition_paths(materials_dir, set_number, run_number)

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
        game_state = game.step(Action.LoadScenario(_load_scenario(
            first_path, subject_id, session_id, block_index=0,
            trial_offset=trial_offset,
        )))
        logger.info("Preloaded first condition %s behind scanner screen", first_label)

        display.hide()
        display.show()
        display.clear()
        display.draw_text("Waiting for scanner — trigger: 5")
        grab_pygame_focus()

        display.await_trigger(in_scanner=not not_in_scanner)
        run_zero_ns = time.perf_counter_ns()
        trigger_utc = datetime.now(timezone.utc).isoformat()
        events = EventFile(
            output_dir, subject_id, session_id, set_number, run_number
        )
        logger.info(
            "Scanner trigger received at %s; events=%s", trigger_utc, events.path
        )

        scheduled_seconds = onset_fixation_seconds
        game_state = _show_fixation(
            display, game, fallback_state=game_state,
            duration_s=onset_fixation_seconds,
            instruction_lines=(
                _practice_fixation_text(RUN_ONSET_FIXATION_SECONDS)
                if practice_mode else None
            ),
            deadline_ns=(
                run_zero_ns + int(onset_fixation_seconds * 1_000_000_000)
            ),
        )

        total_cards_found = 0
        block_scores = []
        for block_index, (label, condition, path) in enumerate(schedule):
            code = _trial_type(condition)
            display.hide()
            restore_unity_focus_after_rating(browser)
            scheduled_seconds += task_seconds
            game_state = _run_task_epoch(
                game, run_zero_ns, code, events, fallback_state=game_state,
                deadline_ns=(
                    run_zero_ns + int(scheduled_seconds * 1_000_000_000)
                ),
            )
            block_score = _completed_instruction_count(game_state)
            block_scores.append(block_score)
            total_cards_found += block_score
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
                player_pose = _player_pose_from_state(game_state)
                next_scenario_data = _load_scenario(
                    next_path, subject_id, session_id,
                    block_index=block_index + 1,
                    trial_offset=trial_offset,
                    player_pose=player_pose,
                )
                scheduled_seconds += fixation_seconds
                game_state = _show_fixation(
                    display, game, fallback_state=game_state,
                    scenario_data=next_scenario_data,
                    duration_s=fixation_seconds,
                    instruction_lines=(
                        _practice_fixation_text(FIXATION_SECONDS)
                        if practice_mode else None
                    ),
                    deadline_ns=(
                        run_zero_ns + int(scheduled_seconds * 1_000_000_000)
                    ),
                )
            else:
                scheduled_seconds += offset_fixation_seconds
                game_state = _show_fixation(
                    display, game, fallback_state=game_state,
                    duration_s=offset_fixation_seconds,
                    instruction_lines=(
                        _practice_fixation_text(RUN_OFFSET_FIXATION_SECONDS)
                        if practice_mode else None
                    ),
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
    parser.add_argument("subject_id", nargs="?")
    parser.add_argument(
        "--session-id",
        help="Naming/metadata identifier; does not affect run settings",
    )
    parser.add_argument("set_number", nargs="?", help="Material set, 1-10")
    parser.add_argument("run_number", nargs="?", help="Landscape run, 1-8")
    parser.add_argument("--materials-dir", default=MATERIALS_DIR)
    parser.add_argument("--output-dir", default="data/events")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--lobby", default=LOBBY)
    parser.add_argument(
        "--browser", choices=("firefox", "chrome"), default="firefox"
    )
    parser.add_argument(
        "--mode", choices=("fmri", "practice", "dry-run"), default="fmri",
        help="Timing and fixation-presentation mode (default: fmri)",
    )
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
    if args.mode == "fmri":
        missing = [
            name for name, value in (
                ("subject_id", args.subject_id),
                ("--session-id", args.session_id),
                ("set_number", args.set_number),
                ("run_number", args.run_number),
            ) if value is None
        ]
        if missing:
            parser.error("fMRI mode requires: " + ", ".join(missing))
    else:
        args.subject_id = args.subject_id or args.mode
        args.session_id = args.session_id or args.mode
        args.set_number = "prac"
        args.run_number = "prac"
        args.pilot_wasd = True
    run_scanner_task(
        args.subject_id, args.session_id, args.set_number, args.run_number,
        materials_dir=args.materials_dir, output_dir=args.output_dir,
        host=args.host, lobby=args.lobby, browser_name=args.browser,
        not_in_scanner=args.not_in_scanner, timing_mode=args.mode,
        pilot_wasd=args.pilot_wasd,
        display_number=args.display_number,
        window_layout=args.window_layout,
    )


if __name__ == "__main__":
    main()
