# CerealBar fMRI Task

The task is controlled by Python, while the visible game is a Unity WebGL game
running in Chrome.

## Task structure

The launcher asks for:

- Task mode
- Participant ID
- Session ID (used only for output naming and metadata)
- Run set
- Optional WASD controls
- Monitor
- Window layout

Python starts a local CB2 game server. Chrome and Unity then load in the
background.

The screen displays:

> Waiting for scanner — trigger: 5

Scanner key `5` starts the timing clock.

Three timing modes are available:

| Launcher choice | Mode | Task block | Between blocks | Onset/offset |
|---|---|---:|---:|---:|
| `1` | fMRI task | 30 s | 10 s | 20 s |
| `2` | practice | 30 s | 3 s | 3 s |
| `3` | test dry run | 3 s | 1 s | 2 s |

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

| Label | Condition |
|---|---|
| `A` | Hard language + fog |
| `B` | Hard language + clear environment |
| `C` | Easy language + fog |
| `D` | Easy language + clear environment |

Each run contains eight 30-second blocks. The condition order is hard-coded by
run set:

| Run sets | Block order |
|---|---|
| `A`, `E` | `D B C A A C B D` |
| `B`, `F` | `D C B A A B C D` |
| `C`, `G` | `D C A B B A C D` |
| `D`, `H` | `D A B C C B A D` |

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

All eight blocks use the same scenario ID and its material-supplied map,
landmark layout, cards, and instructions. At every block boundary, the player's
position and facing direction carry
over continuously from the end of the preceding block. The cards reset, the
unfinished target from the preceding block is discarded, the next target is
initialized, and fog changes when required. Cards completed within the
preceding block are also skipped, so a new block never resumes or repeats the
card that the participant had reached at its boundary.
The common instruction–target order is shuffled reproducibly using participant
ID and map. Hard and easy wording always remains paired with the correct card.

Material files are authoritative. The scanner does not crop or resize their
maps, remove or replace cards/landmarks, rewrite landmark wording, filter
targets, or generate additional instructions. The bundled local folder
currently contains scenario IDs 001–003 for every run set A–H, with eight
condition files per scenario. Unless `--scenario-id` is supplied, the scanner
uses the lowest scenario ID shared by all four conditions.

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

Their names include both identifiers, for example:

```text
sub-001_ses-02_task-cerealbar_runset-A_events.tsv
```

Session ID is also stored in the runtime scenario metadata. It does not affect
the map, instructions, shuffle order, condition order, timing, or other run
settings.

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
