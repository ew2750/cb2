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
    validate_scenario_files,
)
from cb2game.fmri.utils import (
    browser_window_geometry,
    display_layout,
    open_browser,
)
from cb2game.pyclient.game_endpoint import Action
from cb2game.pyclient.remote_client import RemoteClient


logger = logging.getLogger(__name__)
TASK_SECONDS = 30.0
FIXATION_SECONDS = 10.0
RUN_ONSET_FIXATION_SECONDS = 20.0
RUN_OFFSET_FIXATION_SECONDS = 20.0
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
        "onset_fixation": 10.0,
        "offset_fixation": 5.0,
    },
    "dry-run": {
        "task": 30000.0,
        "fixation": 1.0,
        "onset_fixation": 2.0,
        "offset_fixation": 2.0,
    },
}
GAME_POLL_INTERVAL_NS = 50_000_000
EVENT_COLUMNS = ("onset", "duration", "trial_type")
RUNSET_CONDITION_ORDERS = {
    "A": ("D", "B", "C", "A", "A", "C", "B", "D"),
    "E": ("D", "B", "C", "A", "A", "C", "B", "D"),
    "B": ("D", "C", "B", "A", "A", "B", "C", "D"),
    "F": ("D", "C", "B", "A", "A", "B", "C", "D"),
    "C": ("D", "C", "A", "B", "B", "A", "C", "D"),
    "G": ("D", "C", "A", "B", "B", "A", "C", "D"),
    "D": ("D", "A", "B", "C", "C", "B", "A", "D"),
    "H": ("D", "A", "B", "C", "C", "B", "A", "D"),
}


def _safe_label(value):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(value)).strip("-") or "unknown"


class EventFile:
    """Incremental BIDS-compatible event writer using scanner-trigger time zero."""

    def __init__(self, output_dir, subject_id, session_id, run_set):
        output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"sub-{_safe_label(subject_id)}_ses-{_safe_label(session_id)}_"
            f"task-cerealbar_"
            f"runset-{_safe_label(str(run_set).removeprefix('runset_'))}_events.tsv"
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
                     template_number=None, scenario_id=None):
    # A/B/C/D denote HH/EH/HE/EE. The order is fixed by run set and cannot be
    # changed by any external template argument.
    condition_lookup = {
        "A": (hard_environment, hard_language),
        "B": (0, hard_language),
        "C": (hard_environment, 0),
        "D": (0, 0),
    }
    run_set_letter = str(run_set).removeprefix("runset_").upper()
    if run_set_letter not in RUNSET_CONDITION_ORDERS:
        raise ValueError(
            f"Run set must be A-H, received {run_set!r}"
        )
    labels = RUNSET_CONDITION_ORDERS[run_set_letter]
    if template_number is not None:
        logger.warning(
            "Ignoring condition template %s; runset_%s has fixed order %s",
            template_number, run_set_letter, " ".join(labels),
        )
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

    schedule = []
    for label in labels:
        condition = condition_lookup[label]
        entry = next(
            item
            for item in available[condition]
            if item["scenario_id"] == selected_id
        )
        schedule.append((label, condition, Path(entry["full_path"])))
    return schedule


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
        for normalized in [
            _serialized_location(tile.get("cell", {}).get("coord"))
        ]
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
        Path(path).name,
        player_pose["location"],
        player_pose["rotation_degrees"],
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
    scenario["kvals"]["fmri_auto_advance_instructions"] = True
    _apply_player_pose(scenario, player_pose, path)

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
    seed_text = f"{subject_id}:{material_key}"
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
        # Loading a new Unity scenario can cause the browser to repaint or
        # reclaim focus on macOS. Raise and redraw the fixation immediately.
        _draw_fixation(display, instruction_lines)
        grab_pygame_focus()
    latest_state = _wait_until(
        deadline_ns, game=game, fallback_state=fallback_state
    )
    duration = (time.perf_counter_ns() - start_ns) / 1_000_000_000
    logger.info("Fixation finished after %.6f seconds", duration)
    return latest_state


def run_scanner_task(subject_id, session_id, run_set, hard_environment,
                     hard_language, materials_dir=MATERIALS_DIR,
                     output_dir="data/events", template_number=None,
                     scenario_id=None, host=HOST, lobby=LOBBY,
                     browser_name="firefox", not_in_scanner=False,
                     timing_mode="fmri",
                     pilot_wasd=False, display_number=1, window_layout=1):
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

    run_set = run_set if str(run_set).startswith("runset_") else f"runset_{run_set}"
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
                    first_path, subject_id, session_id, block_index=0,
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
        events = EventFile(output_dir, subject_id, session_id, run_set)
        logger.info("Scanner trigger received at %s; events=%s", trigger_utc, events.path)

        scheduled_seconds = onset_fixation_seconds
        game_state = _show_fixation(
            display, game, fallback_state=game_state,
            duration_s=onset_fixation_seconds,
            instruction_lines=(
                _practice_fixation_text(RUN_ONSET_FIXATION_SECONDS)
                if practice_mode else None
            ),
            deadline_ns=(
                run_zero_ns
                + int(onset_fixation_seconds * 1_000_000_000)
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
    parser.add_argument("subject_id")
    parser.add_argument(
        "--session-id", required=True,
        help="Naming/metadata identifier; does not affect run settings",
    )
    parser.add_argument("run_set")
    parser.add_argument("hard_environment", type=int, help="Hard fog value (normally 3)")
    parser.add_argument("hard_language", type=int, help="1 for hard language")
    parser.add_argument("--materials-dir", default=MATERIALS_DIR)
    parser.add_argument("--output-dir", default="data/events")
    parser.add_argument(
        "--condition-template", type=int, choices=range(1, 5),
        help="Deprecated and ignored; condition order is fixed by run set",
    )
    parser.add_argument("--scenario-id", type=int)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--lobby", default=LOBBY)
    parser.add_argument("--browser", choices=("firefox", "chrome"), default="firefox")
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
    run_scanner_task(
        args.subject_id, args.session_id, args.run_set,
        args.hard_environment, args.hard_language,
        materials_dir=args.materials_dir, output_dir=args.output_dir,
        template_number=args.condition_template, scenario_id=args.scenario_id,
        host=args.host, lobby=args.lobby, browser_name=args.browser,
        not_in_scanner=args.not_in_scanner, timing_mode=args.mode,
        pilot_wasd=args.pilot_wasd,
        display_number=args.display_number,
        window_layout=args.window_layout,
    )


if __name__ == "__main__":
    main()
