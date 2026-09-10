# CerealBar fMRI Task

This experiment integrates CerealBar2 (or CB2), found at [`cb2.ai`](http://cb2.ai/) with an fMRI experiment about the language and working memory/multiple-demand systems. In this directory we house code specifically pertaining to running the experiment in an fMRI scanner. The parent directory is a fork of the [cb2 repository](https://github.com/lil-lab/cb2), also found at [https://github.com/EvLab-MIT/cb2](https://github.com/EvLab-MIT/cb2).

The task is controlled by Python, while the visible game is a Unity WebGL game
running in Chrome.

The current branch contains a easy macOS installation version and task setup GUI.

## Running on macOS

1. Double-click `macos/Install CerealBar fMRI.command` once.
2. Double-click `macos/Run CerealBar fMRI.command` for each run.
3. Choose mode 1 (fMRI), 2 (practice), or 3 (test dry run). fMRI mode then asks
   for participant ID, session ID, material set (`1`–`10`), run (`1`–`8`),
   monitor, and layout. Practice and dry-run modes automatically use
   `set_prac/run_prac`, WASD, display 1, and layout 1.
   The scanner reads the block order from the selected set's
   `condition_order.txt`.
4. When ready (after the game is loaded), press key `5`.

## Running on Linux

1. Run `linux/Install CerealBar fMRI.sh` once.
2. Run `linux/Run CerealBar fMRI.sh` for each run.
3. Choose the same fMRI, practice, or dry-run mode as on macOS.
4. The Linux launcher uses the same Python task runner, same materials
   structure, same event format, and same browser-based Unity game.

## Task structure

Three timing modes are available:


| Launcher choice | Mode         | Task block | Between blocks | Onset/offset |
| --------------- | ------------ | ---------: | -------------: | -----------: |
| `1`             | fMRI task    |       30 s |           10 s |         20 s |
| `2`             | practice     |       30 s |            3 s |          3 s |
| `3`             | test dry run |        3 s |            1 s |          2 s |

The fMRI task and test dry run display a centered `+` during fixation. Practice
mode instead displays a short explanation that the actual task will show a `+`
for 10 seconds between blocks or 20 seconds at run onset/offset, and asks the
participant to rest and keep still.

The four experimental conditions are:

1. Hard language + fog
2. Hard language + clear environment
3. Easy language + fog
4. Easy language + clear environment

For counterbalancing, these are labeled `A`, `B`, `C`, and `D` in this order:


| Label | Condition                         |
| ----- | --------------------------------- |
| `A`   | Hard language + fog               |
| `B`   | Hard language + clear environment |
| `C`   | Easy language + fog               |
| `D`   | Easy language + clear environment |

Each run contains eight 30-second blocks. Each set's `condition_order.txt`
contains a separate order for `run1` through `run8`; the scanner reads the
selected run's order at runtime. Every set uses all six possible D-first
palindromic orders, plus two counterbalanced repeats. Their run assignments are
varied between sets.

Every order begins with `D`, the easy-environment/easy-language condition.

The complete timeline is:

```text
20 s onset fixation
→ 30 s task → 10 s fixation
→ 30 s task → 10 s fixation
→ 30 s task → 10 s fixation
→ 30 s task → 10 s fixation
→ 30 s task → 10 s fixation
→ 30 s task → 10 s fixation
→ 30 s task → 10 s fixation
→ 30 s task
→ 20 s offset fixation
```

Therefore, a complete run contains:

- 8 task blocks × 30 seconds = 240 seconds
- 7 inter-block fixations × 10 seconds = 70 seconds
- 20-second onset fixation + 20-second offset fixation = 40 seconds
- 350 seconds total = 5 minutes 50 seconds

All eight blocks use the selected run's material-supplied map, landmark layout, cards, and instructions. At every block boundary, the player's position and facing direction carry over continuously from the end of the preceding block. The cards reset, the unfinished target from the preceding block is discarded, the next target is initialized, and fog changes when required. Cards completed within the preceding block are also skipped, so a new block never resumes or repeats the
card that the participant had reached at its boundary.
The instruction–target order stored in the material is preserved. Hard and easy wording always remains paired with the correct card.

Material files are pre-set. They use this naming structure:

```text
materials/
  set1/
    condition_order.txt
    run1_env_easy_lang_easy.json
    run1_env_easy_lang_hard.json
    run1_env_hard_lang_easy.json
    run1_env_hard_lang_hard.json
    ...
    run8_env_hard_lang_hard.json
  ...
  set10/
  set_prac/
    condition_order.txt
    run_prac_env_easy_lang_easy.json
    ...
```

## Reproducbility

All materials are preset and task order fixed in `materials`.

`sample.py` generates 10 sets × 8 runs = **80 unique landscapes**, with four condition files per landscape (320 JSON files total). Pink cards are removed, pink-house tiles are replaced with ordinary path tiles. The bundled local folder must be generated into the new `materials/set1`–`set10` structure before this runner is used.

## Python software

The main Python program is:

```text
cb2game.fmri.scanner_task
```

It performs the following jobs:

- Displays the scanner-waiting screen
- Detects trigger key `5` or `t`
- Controls the 20/30/10-second timing
- Changes experimental conditions
- Displays fixation crosses
- Loads instructions in their material-defined order
- Moves Chrome to the chosen monitor
- Controls the game-window size
- Focuses Chrome automatically
- Writes event files
- Counts correctly selected cards and displays the total when the run end

The project uses Python 3.9 inside:

```text
<repo>/.venv
```

Important Python packages include:

- `pygame`: waiting and fixation screens
- `selenium`: launches and controls Chrome
- `aiohttp`: local game-server communication
- `orjson`: fast game-message processing

## Unity's role

Unity renders:

- The map
- Cards and landmarks
- Fog
- Player movement
- Instructions
- Card-selection feedback

During scanner runs, Python places a high-contrast HTML instruction panel over
the Unity panel on the left. The active instruction is synchronized from the
game state and displayed in bold black Arial-compatible text. Because this
overlay is ordinary HTML, its appearance can be adjusted in
`src/cb2game/server/www/WebGL/TemplateData/style.css` without rebuilding
Unity.

Python does not render the game world. It controls the experiment surrounding
the Unity game.

## Key controls


| Key | Action      |
| --- | ----------- |
| `4` | Forward     |
| `3` | Turn left   |
| `6` | Backward    |
| `1` | Turn right  |
| `2` | Pick up card |

Optional pilot controls:


| Key | Action      |
| --- | ----------- |
| `W` | Forward     |
| `S` | Backward    |
| `A` | Left        |
| `D` | Right       |
| `2` | Pick up card |

## Event data

Event files are saved in:

```text
<repo>/data/events
```

Their names include both identifiers, for example:

```text
sub-001_ses-02_task-cerealbar_set-01_run-01_events.tsv
```

Session ID is also stored in the runtime scenario metadata. It does not affect
the map, instructions, condition order, timing, or other run
settings.

Each `.tsv` file contains:


| Column       | Description                        |
| ------------ | ---------------------------------- |
| `onset`      | Seconds after the scanner trigger  |
| `duration`   | Measured task-epoch duration       |
| `trial_type` | Language and environment condition |

A completed run should contain 8 event rows. The 20-second onset/offset
fixations and seven inter-block fixations are not written as task events.
If the same identifiers are used again, the existing file is preserved and a
new `_repeat-02`, `_repeat-03`, and so on file is created.

Other local game data is stored in `<repo>/data/server`, and the latest server
log is stored in `<repo>/data/server.log`.

# 20260818 CB2 fMRI task changes from the original repository

- Added a macOS installer and one-command launcher for the local Python server, Chrome, and Unity WebGL task.
- Made the task single-player and local-only; removed participant-facing online, follower/leader, matchmaking, rating, and feedback steps.
- Covered Unity startup with a scanner-wait screen, added trigger key `5`, kept one Unity session/map for the whole run, and logged monotonic trigger-relative event timing.
- Added fMRI, practice, and dry-run timing modes. An fMRI run is eight task blocks with 20-second onset/offset and 10-second inter-block fixations (350 seconds total).
- Added automatic window focus, monitor/layout selection, scanner controls `2/3/4/5/6`, and automatic WASD controls for practice/dry runs.
- Preserved player position and heading between blocks, discarded the active target at each boundary, retained the instruction/target order supplied by the materials, and displayed the final correct-card score.
- Added non-overwriting session-labelled event files and runtime metadata.
- Reorganized materials as `set1`–`set10`, `run1`–`run8`, plus `set_prac/run_prac`; retained only the four named 2×2 condition files. The material JSON files define the clear and hard-fog distances.
- Reduced generated maps to 12 × 12, with 15 target cards and 2 distractors per target instruction.
- Moved each set's eight-block order to `condition_order.txt` that is within each set materials; Python reads and validates it.
- Removed pink cards and pink-house tiles from scanner materials. The generator excludes pink content and preserves the local material map size/layout.
