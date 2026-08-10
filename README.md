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

Four experimental conditions run:

1. Easy language + clear environment
2. Hard language + clear environment
3. Easy language + fog
4. Hard language + fog

Each condition contains:

```text
30 s task → 10 s fixation → 30 s task → 10 s fixation → 30 s task → 10 s fixation
```

Therefore, a complete run contains:

- 4 conditions
- 3 task epochs per condition
- 12 task epochs
- 12 fixation periods
- 8 minutes of scheduled task time

The order of the four conditions is counterbalanced. Instructions and their
corresponding target cards are shuffled together using the participant ID, run
number, and condition.

## Python software

The main Python program is:

```text
cb2game.fmri.scanner_task
```

It performs the following jobs:

- Displays the scanner-waiting screen
- Detects trigger key `5`
- Controls the 30/10-second timing
- Changes experimental conditions
- Displays fixation crosses
- Loads and shuffles instructions
- Moves Chrome to the chosen monitor
- Controls the game-window size
- Focuses Chrome automatically
- Writes event files

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

A completed run should contain 12 event rows.

Other local game data is stored in `/Users/exw/projects/cb2/data/server`, and
the latest server log is stored in `/Users/exw/projects/cb2/data/server.log`.
