# CerealBar fMRI Task

The task is controlled by Python, while the visible game is a Unity WebGL game
running in Chrome.

## Task structure

The launcher asks for:

- Participant ID
- Run number
- Run set
- Condition-order template
- Optional WASD controls
- Monitor
- Window layout

Python starts a local CB2 game server. Chrome and Unity then load in the
background.

The screen displays:

> Waiting for scanner — trigger: 5

Scanner key `5` starts the timing clock.

The four experimental conditions are:

1. Hard language + fog
2. Hard language + clear environment
3. Easy language + fog
4. Easy language + clear environment

For counterbalancing, these are labeled `A`, `B`, `C`, and `D` in this order:

| Label | Condition |
|---|---|
| `A` | Hard language + fog |
| `B` | Hard language + clear environment |
| `C` | Easy language + fog |
| `D` | Easy language + clear environment |

Each run contains eight 30-second blocks in a palindrome. The four templates
are:

| Template | Block order |
|---|---|
| `1` | `A B C D D C B A` |
| `2` | `B C D A A D C B` |
| `3` | `C D A B B A D C` |
| `4` | `D A B C C B A D` |

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

All eight blocks use the same 12 × 12 map, landmark layout, and non-pink card
set. At every block boundary, the player is placed at a new randomized safe
position and heading on the same map, the cards reset, the unfinished target
from the preceding block is discarded, the next target is initialized, and fog
changes when required. Spawn positions exclude cards, landmarks, blocked cells,
and isolated parts of the map. Cards completed within the preceding block are
also skipped, so a new block never resumes or repeats the card that the
participant had reached at its boundary.
The common instruction–target order is shuffled reproducibly using participant
ID, run number, and map. Hard and easy wording always remains paired with the
correct card. Spawn randomization is likewise reproducible from participant ID,
run number, map, and block number, allowing a run to be audited or repeated.

Pink cards and the pink-house landmark are excluded because they are visually
confusing. A removed pink house is replaced by `GROUND_TILE_PATH` (asset ID 28).
All light landmarks are called “lamppost” in task instructions.

Only scenario 001 is retained in run sets A–H, with eight condition files per
run set. For E and F, the better filtered scenario 003 layouts were promoted
and renamed to scenario 001; their previous scenario 001/002 layouts were
removed. Every run set now has 18 target–instruction pairs; retained ground-card
counts are A 59, B 60, C 56, D 52, E 59, F 59, G 57, and H 53.
Material-audit history is recorded in
`SCENARIO_0001_12X12_AUDIT.md` and
`SCENARIO_EF_003_PROMOTED_TO_001_AUDIT.md`.
The complete current target IDs, unique card attributes, landmark chains, and
paired easy/hard instructions for A–H are recorded in
`ALL_RUNSETS_TARGET_AUGMENTATION_AUDIT.md`.

## Python software

The main Python program is:

```text
cb2game.fmri.scanner_task
```

It performs the following jobs:

- Displays the scanner-waiting screen
- Detects trigger key `5`
- Controls the 20/30/10-second timing
- Changes experimental conditions
- Displays fixation crosses
- Loads and shuffles instructions
- Moves Chrome to the chosen monitor
- Controls the game-window size
- Focuses Chrome automatically
- Writes event files
- Counts correctly selected cards and displays the total when the run ends

The launcher starts it with approximately:

```bash
.venv/bin/python -m cb2game.fmri.scanner_task
```

The project uses Python 3.9 inside:

```text
/Users/exw/projects/cb2/.venv
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

Python does not render the game world. It controls the experiment surrounding
the Unity game.

## Controls

| Key | Action |
|---|---|
| `2` | Forward |
| `3` | Backward |
| `4` | Turn left |
| `5` | Turn right |
| `6` | Select card |

Optional pilot controls:

| Key | Action |
|---|---|
| `W` | Forward |
| `S` | Backward |
| `A` | Left |
| `D` | Right |
| `6` | Select card |

## Event data

Event files are saved in:

```text
/Users/exw/projects/cb2/data/events
```

Each `.tsv` file contains:

| Column | Description |
|---|---|
| `onset` | Seconds after the scanner trigger |
| `duration` | Measured task-epoch duration |
| `trial_type` | Language and environment condition |

A completed run should contain 8 event rows. The 20-second onset/offset
fixations and seven inter-block fixations are not written as task events.

Other local game data is stored in `/Users/exw/projects/cb2/data/server`, and
the latest server log is stored in `/Users/exw/projects/cb2/data/server.log`.
