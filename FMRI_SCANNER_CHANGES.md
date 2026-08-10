# CerealBar fMRI scanner build

## What changed

This branch now has a scanner-specific entry point, `cb2-fmri`, and two
double-clickable macOS helpers in `macos/`.

### macOS installation and local-only operation

- `macos/Install CerealBar fMRI.command` creates a private Python environment
  inside the project and installs the runner and its dependencies. It selects
  macOS system Python 3.9 (rather than incompatible newer Python installations),
  and the Apple PyObjC packages are pinned to prebuilt Apple Silicon-compatible
  version 9.2 wheels.
- `macos/Run CerealBar fMRI.command` prompts for the participant/run settings,
  starts the internal CB2 state engine, launches the task, and stops the engine
  when the run finishes.
- The launcher binds the internal HTTP/WebSocket transport to `127.0.0.1`.
  It cannot accept players from another computer and does not use CB2's public
  server, matchmaking, login, leaderboard, leader, or feedback flows.
- The participant enters the scenario directly as the sole visible player.
  Legacy CB2 code calls this controllable searcher `FOLLOWER`; that internal
  compatibility name remains, but no follower/leader choice or second human
  role is exposed in the scanner task.

### Persistent run and splash behavior

- The first scenario is preloaded while the black “Waiting for scanner” screen
  covers the Unity client.
- The browser and Unity instance remain open for the entire run. Scenario
  changes are loaded into the existing game instance, so Unity is not restarted
  and its loading/splash screen cannot appear between task blocks.
- Unity Player Settings disable the Unity splash screen and use the product
  name `CerealBar fMRI`. Unity Personal may enforce Unity branding at process
  startup depending on the installed Unity license; the scanner waiting screen
  covers startup regardless. A license that permits disabling the splash is
  required for a native rebuilt player to omit it at the engine level.

### Scanner timing

- The initial screen is black and reads `Waiting for scanner — trigger: 5`.
- After Chrome and Unity finish loading, the scanner display is recreated and
  raised to the front. Unity is already ready behind it; pressing `5` dismisses
  the waiting screen rather than initiating the load.
- The scanner trigger is keyboard key `5`. Before the trigger it starts the
  run; after the waiting screen closes, key `5` is the turn-right control.
- A run contains the four counterbalanced 2×2 conditions. Each condition is:

  1. 30.000 seconds of active task
  2. 10.000 seconds of black fixation with a centered white `+`
  3. 30.000 seconds of active task
  4. 10.000 seconds of black fixation with a centered white `+`
  5. 30.000 seconds of active task
  6. 10.000 seconds of black fixation with a centered white `+`

- The next condition is loaded in the background during the fixation after the
  third task epoch. The cross therefore remains visible throughout the
  condition transition. The participant's map pose is carried across condition
  changes; condition-specific cards and instructions reset from the matching
  material file.
- Timing uses `time.perf_counter_ns()`, a monotonic nanosecond clock. Time zero
  is captured immediately after receipt of the scanner trigger. Actual measured
  onsets/durations are logged rather than planned values.
- Task and fixation clocks use that local clock only. They drain already
  buffered game messages to maintain the connection, but do not call the
  blocking game-step API because it can wait up to 60 seconds when no state tick
  is produced. The fixation overlay is also hidden before browser focus is
  restored, so a delayed browser response cannot extend the visible fixation.

### Controls

| Key | Action |
|---|---|
| `2` | forward |
| `3` | backward |
| `4` | turn left |
| `5` | turn right (and scanner trigger only on the waiting screen) |
| `6` | pick up / select card |

The mappings are present both in Unity source and as a runtime translation for
the bundled WebGL build.

For pilot testing, the launcher optionally enables `W`/`S`/`A`/`D` for
forward/back/left/right. In that mode, pickup remains key `6`; physical `S` is
used only for backward movement.

After a correct target card is selected, the fMRI scenario now automatically
marks the active instruction complete and displays the next instruction. This
behavior is enabled only for scenarios loaded by the fMRI runner.

Each instruction has one target card. If a participant first selects the wrong
card and then selects a different card, the new selection replaces the old one;
the participant does not need to manually deselect the first card. A correct
second attempt therefore advances immediately.

Instruction order is shuffled as linked `(instruction, target card)` pairs for
every condition. The order is reproducible from participant ID, run number, and
condition material path, and the resulting target-card order is stored in the
scenario metadata/log for auditability.

### Events file

One tab-separated BIDS-style event file is created per run in
`cb2/data/events`:

`sub-<participant>_task-cerealbar_run-<run>_events.tsv`

It contains exactly these columns:

| Column | Meaning |
|---|---|
| `onset` | task-epoch onset in seconds relative to scanner trigger |
| `duration` | measured task-epoch duration in seconds |
| `trial_type` | explicit 2×2 condition, for example `language-hard_environment-fog` |

Each row is flushed and synced to disk immediately. A complete four-condition
run produces twelve task-event rows. Fixations are not included because the
requested event type is the 30-second task epoch. Repeating the same participant
and run number creates a `_repeat-02` file instead of overwriting prior data.

All run data now stays inside the project folder:

- `data/events/` contains the per-run BIDS-style event files.
- `data/server/` contains the local game database, records, and server assets.
- `data/server.log` contains the server log from the latest launch.

The launcher creates these directories automatically. Move or copy the whole
`data/` directory when transferring results off the scanner computer.

### Large-window presentation

- Chrome opens as a large normal `1280 × 800` window, not in macOS fullscreen
  mode. This avoids switching between macOS fullscreen Spaces.
- The WebGL container and Unity canvas fill the browser viewport, rather than
  using the previous smaller fixed-aspect container.
- Scanner waiting and fixation displays use pygame fullscreen and are raised
  above the already-loaded Unity game only when required.
- The Mac launcher asks for a display number. Display `1` is the primary screen;
  display `2` is normally the first extended monitor. The Unity window, scanner
  waiting screen, and every fixation are placed on the selected display.
- The selected display's usable dimensions are measured at launch. The launcher
  then offers three Unity window layouts: maximum usable size without macOS
  fullscreen, the upper two-thirds of the screen, or a centered window using
  50% of the screen width and height.
- The Unity UI reference resolution is increased from `1000 × 600` to
  `1250 × 750`, rendering interface elements at approximately 80% of their
  previous size. The overhead camera maintains approximately 10% padding on all
  viewport edges, producing a zoomed-out view that reveals more cards and
  landmarks.
- Until a locally activated Unity license is available to rebuild the WebGL
  binary, the scanner runner also applies Chrome's 80% page zoom to the bundled
  client. This immediately reduces interface obstruction in the current build;
  the source-level camera change takes effect on the next licensed rebuild.

## Running on a Mac

1. Double-click `macos/Install CerealBar fMRI.command` once.
2. Double-click `macos/Run CerealBar fMRI.command` for each run.
3. Enter participant ID, run number, run set (`A` through `H`), and optionally
   a condition template (`1` through `4`).
4. When the scanner is ready, send key `5`.

The launcher uses hard environment level `3` and hard language level `1`; easy
variants are level `0`. It chooses the same scenario ID across all conditions,
using the lowest common ID unless explicitly set through the command-line API.

For laptop testing, run:

```bash
.venv/bin/python -m cb2game.fmri.scanner_task \
  TEST 1 A 3 1 --not-in-scanner --browser chrome \
  --host http://127.0.0.1:8080
```

The local server must already be running for this direct command. The
double-clickable launcher starts it automatically.

## Files changed

- `src/cb2game/fmri/scanner_task.py`: persistent scanner protocol and events
- `src/cb2game/fmri/main.py`: black waiting/fixation display and trigger `5`
- `src/cb2game/fmri/utils.py`: fullscreen browser startup
- `src/cb2game/server/main.py`: optional loopback-only binding
- `src/cb2game/server/www/WebGL/TemplateData/style.css`: viewport-filling game
- `macos/*.command`: one-time installer and per-run launcher
- `cb2fmri.yaml`: project-local server database and record directory
- `pyproject.toml`: `cb2-fmri` command and runtime package metadata

## Runtime-only cleanup (2026-08-09)

The project folder was reduced to the files needed to install and run the Mac
scanner task. The retained top-level contents are `src/`, `macos/`, `data/`,
`cb2fmri.yaml`, `pyproject.toml`, this change note, and the license. The
extracted `src/cb2game/server/www/WebGL/` build is retained and served locally.

Development-only material was moved, not permanently deleted. This includes
the Git history, Unity Editor source project, Linux environment and build
files, development notebook/configuration, stale generated logs and data,
Python caches, and the redundant `WebGL.zip`. On the cleanup computer it can be
restored from:

`/Users/exw/Documents/Codex/archives/cb2-nonruntime-20260809`

The Unity source in that archive contains the source-level scanner changes;
the runnable project uses their compiled WebGL output. Restore the archived
Unity project and Git metadata only if future Unity development or rebuilding
is required.
