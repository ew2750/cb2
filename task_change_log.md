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

### Large-window presentation

- Chrome opens as a large normal window sized from the selected monitor, not
  in macOS fullscreen mode. This avoids switching between macOS fullscreen
  Spaces.
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
  binary, the scanner runner also applies Chrome's 67% page zoom to the bundled
  client. This immediately reduces interface obstruction in the current build;
  the source-level camera change takes effect on the next licensed rebuild.

## Files changed

- `src/cb2game/fmri/scanner_task.py`: persistent scanner protocol and events
- `src/cb2game/fmri/main.py`: black waiting/fixation display and trigger `5`
- `src/cb2game/fmri/utils.py`: fullscreen browser startup
- `src/cb2game/server/main.py`: optional loopback-only binding
- `src/cb2game/server/www/WebGL/TemplateData/style.css`: viewport-filling game
- `macos/*.command`: one-time installer and per-run launcher
- `cb2fmri.yaml`: project-local server database and record directory
- `pyproject.toml`: `cb2-fmri` command and runtime package metadata

## Eight-block protocol revision (2026-08-13)

A complete pre-change copy, including the Git repository, Python environment,
materials, and compiled client, was saved before this revision at:

`/Users/exw/Documents/Codex/backups/cb2-before-palindrome-20260813`

This revision introduced the eight-block schedule, exact fMRI timeline, shared
scenario across blocks, wider browser view, and end-of-run card score.

### Local-material authority revision (2026-08-14)

The earlier runtime crop, terminology rewriting, and manual target
augmentation were retired. The scanner loads maps, props, landmarks, and
instruction text directly from `src/cb2game/fmri/materials`. The former A–H
scenario layout was superseded by the ten-set/eight-run redesign below.

### Ten-set/eight-run material redesign (2026-08-17)

A full pre-change backup was saved at:

`/Users/exw/projects/cb2_backup_2026-08-17_before_set_run_redesign`

`sample.py` now targets `set1`–`set10`, with `run1`–`run8` inside each set.
Each run produces only the four named clear/fog × easy/hard language files.
This is 80 unique base landscapes and 320 condition JSON files, plus four
practice files. Each set has a human-editable `condition_order.txt`, which is
the scanner runner's sole source for block order. It defines separate orders
for `run1` through `run8`; each set uses all six D-first palindromic orders plus
two counterbalanced repeats, with assignments varied between sets. Generated
materials reject pink cards and instructions and replace any pink-house tile
with a normal path tile.

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
