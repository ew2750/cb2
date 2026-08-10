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


logger = logging.getLogger(__name__)
TASK_SECONDS = 30.0
FIXATION_SECONDS = 10.0
EPOCHS_PER_CONDITION = 3
GAME_POLL_INTERVAL_NS = 50_000_000
EVENT_COLUMNS = ("onset", "duration", "trial_type")


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

    result = []
    for label in labels:
        condition = condition_lookup[label]
        entry = next(
            item
            for item in available[condition]
            if item["scenario_id"] == selected_id
        )
        result.append((label, condition, Path(entry["full_path"])))
    return result


def _load_scenario(path, subject_id, run_number, previous_state=None):
    with Path(path).open(encoding="utf-8") as handle:
        scenario = json.load(handle)
    scenario.setdefault("subject", {}).update(
        {"subject_id": str(subject_id), "run": int(run_number)}
    )
    scenario["kvals"] = scenario.get("kvals") or {}
    scenario["kvals"]["fmri_auto_advance_instructions"] = True

    objectives = scenario.get("objectives", [])
    target_groups = scenario.get("target_card_ids", [])
    if len(objectives) != len(target_groups):
        raise ValueError(
            f"Instruction/target count mismatch in {path}: "
            f"{len(objectives)} instructions, {len(target_groups)} targets"
        )
    paired_trials = list(zip(objectives, target_groups))
    material_key = f"{Path(path).parent.name}/{Path(path).name}"
    seed_text = f"{subject_id}:{run_number}:{material_key}"
    shuffle_seed = int.from_bytes(
        hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big"
    )
    random.Random(shuffle_seed).shuffle(paired_trials)
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
                f"cb2-fmri:{Path(path).resolve()}:{subject_id}:{run_number}:{index}",
            ))
    scenario["duration_s"] = 3600

    # Keep only the participant's pose across condition changes. Objectives and
    # cards reset to the condition-specific materials.
    if previous_state is not None:
        state = previous_state.to_dict()
        source = next(
            (actor for actor in state.get("actors", [])
             if actor.get("actor_role") == 1),
            None,
        )
        if source is not None:
            target = next(
                (actor for actor in scenario.get("actor_state", {}).get("actors", [])
                 if actor.get("actor_role") == 1),
                None,
            )
            if target is not None:
                target["location"] = source.get("location", target.get("location"))
                target["rotation_degrees"] = source.get(
                    "rotation_degrees", target.get("rotation_degrees", 0)
                )
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
    """Set Chrome to 80% page zoom so the bundled UI occupies less space."""
    try:
        from selenium.webdriver import ActionChains
        from selenium.webdriver.common.keys import Keys

        before = browser.execute_script(
            "return [window.innerWidth, window.innerHeight];"
        )
        ActionChains(browser).key_down(Keys.COMMAND).send_keys("-").send_keys(
            "-"
        ).key_up(Keys.COMMAND).perform()
        time.sleep(0.2)
        after = browser.execute_script(
            "return [window.innerWidth, window.innerHeight];"
        )
        logger.info("Applied 80%% interface zoom: viewport %s -> %s", before, after)
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
                    fallback_state=None):
    onset_ns = time.perf_counter_ns()
    deadline_ns = onset_ns + int(TASK_SECONDS * 1_000_000_000)
    latest_state = _wait_until(
        deadline_ns, game=game, fallback_state=fallback_state
    )
    offset_ns = time.perf_counter_ns()
    onset = (onset_ns - run_zero_ns) / 1_000_000_000
    duration = (offset_ns - onset_ns) / 1_000_000_000
    event_file.append(onset, duration, condition_code)
    logger.info(
        "Logged %s onset=%.6f duration=%.6f", condition_code, onset, duration
    )
    return latest_state


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


def _show_fixation(display, game, fallback_state=None, scenario_data=None):
    display.show_cross()
    grab_pygame_focus()
    start_ns = time.perf_counter_ns()
    deadline_ns = start_ns + int(FIXATION_SECONDS * 1_000_000_000)
    logger.info("Fixation started; deadline is %.3f seconds", FIXATION_SECONDS)
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

        first_label, _, first_path = schedule[0]
        game_state = game.step(
            Action.LoadScenario(
                _load_scenario(first_path, subject_id, run_number)
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

        for condition_index, (label, condition, path) in enumerate(schedule):
            code = _trial_type(condition)
            for epoch_index in range(EPOCHS_PER_CONDITION):
                display.hide()
                restore_unity_focus_after_rating(browser)
                game_state = _run_task_epoch(
                    game, run_zero_ns, code, events, fallback_state=game_state
                )

                next_scenario_data = None
                if (
                    epoch_index == EPOCHS_PER_CONDITION - 1
                    and condition_index + 1 < len(schedule)
                ):
                    _, _, next_path = schedule[condition_index + 1]
                    next_scenario_data = _load_scenario(
                        next_path, subject_id, run_number,
                        previous_state=game_state,
                    )
                game_state = _show_fixation(
                    display, game, fallback_state=game_state,
                    scenario_data=next_scenario_data,
                )

        display.show_complete()
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
