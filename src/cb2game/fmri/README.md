# EXPT_CerealBar2

This experiment integrates CerealBar2 (or CB2), found at [`cb2.ai`](http://cb2.ai) with an fMRI experiment 
about the language and working memory/multiple-demand systems. In this directory we house code specifically 
pertaining to running the experiment in an fMRI scanner. The parent directory is a fork of the 
[cb2 repository](https://github.com/lil-lab/cb2), also found at https://github.com/EvLab-MIT/cb2.


# Usage

## Scanner-ready Mac runner (recommended)

The current scanner protocol, controls, Mac installation instructions, timing,
and event-file specification are documented in
[`FMRI_SCANNER_CHANGES.md`](../../../FMRI_SCANNER_CHANGES.md). On macOS,
double-click `macos/Install CerealBar fMRI.command` once and then use
`macos/Run CerealBar fMRI.command` for each scan run.

The sections below describe the legacy research runner and are retained for
reproducibility.

There are two components to running this experiment.

## 1. CB2 game server

Ensure you are in the conda environment you used to clone cb2 when doing this step. If you have not set up a conda environment, refer to the main README for cb2, or do so with the following command:
```bash
conda create -n cb2env python=3.11
conda activate cb2env
```

In one terminal, parallelly run an instance of the
`cb2` server that we can interact with and use to serve scenarios (refer to [parent README](../README.md) for more info). Use the cb2fmri.yaml found in the cb2 directory: 
```bash
python -m cb2game.server.main --config_filepath=cb2fmri.yaml
```

You can now access the game instance at `http://localhost:8080/`

If the server does not run, try running the following command first to set up the Unity client:
```bash
python -m cb2game.server.fetch_client
```

## 2. CB2 experiment driver

The experiment driver program is run as a module from the parent directory. Open a new terminal in the same conda environment. Move to the src directory, which should contain the cb2game package. Start the experiment with the following command:
```bash
python -m cb2game.fmri.main <ARGS>
```

`<ARGS>` should contain parameters for `subject_id`, `run_number`, `run_set`, `task_difficulty`, and `linguistic_complexity`.

### Behavioral mode (palindrome protocol)

Use `--behavioral` to run the fixed-timing palindrome FMRI protocol.

- `run_set`: pass `A` (auto-converted to `runset_A`) or pass `runset_A` directly.
- `task_difficulty`: use `3` for hard fog (H setting), `0` for easy fog (E setting).
- `linguistic_complexity`: binarized (`0` = easy language, any nonzero = hard language).
- `--condition-template N`: choose predefined forward condition order (`N` in `1-4`).
  - If omitted, template is selected by `run_number`.
- `--scenario-id ID`: pin to a specific shared `scenario_id` across HH/EH/HE/EE.
  - If omitted, the lowest shared `scenario_id` is used.
- `--no-ratings`: disable post-condition rating prompts.
- `--no-test-button-box`: skip the buttonbox practice intro.
  - If using the buttonbox test on a laptop, the key mappings are as follows:
  - Up: 2 | Down: 3 | Right: 7 | Left: 8 | Select: 1

Condition template mapping (`--condition-template`):

| Template | Forward order | One palindrome (`forward + reverse`) |
|---|---|---|
| 1 | `HH, EH, HE, EE` | `HH, EH, HE, EE, EE, HE, EH, HH` |
| 2 | `EH, HE, EE, HH` | `EH, HE, EE, HH, HH, EE, HE, EH` |
| 3 | `HE, EE, HH, EH` | `HE, EE, HH, EH, EH, HH, EE, HE` |
| 4 | `EE, HH, EH, HE` | `EE, HH, EH, HE, HE, EH, HH, EE` |

Legend: `H` setting = `task_difficulty > 0`; `E` setting = `task_difficulty = 0`. `H` language = `linguistic_complexity > 0`; `E` language = `linguistic_complexity = 0`.

Examples:

```bash
# Default behavioral run (template from run_number, lowest shared scenario_id)
python -m cb2game.fmri.main 1 1 A 3 1 --behavioral

# Explicit template and scenario selection
python -m cb2game.fmri.main 1 1 A 3 1 --behavioral --condition-template 2 --scenario-id 1

# Skip both ratings and buttonbox test
python -m cb2game.fmri.main 1 1 A 3 1 --behavioral --no-ratings --no-test-button-box
```

### macOS notes

On the `mac` branch, behavioral runs default to the Mac-friendly scanner protocol:

- waits for scanner trigger key `5` at startup
- skips the buttonbox practice unless `--test-button-box` is passed
- skips post-condition ratings unless `--ratings` is passed
- uses `~/cb2main-old/materials` unless `--materials-dir` or `CB2_MATERIALS_DIR` is set
- launches Firefox by default; use `--browser chrome` or `CB2_BROWSER=chrome` for Chrome

The dedicated `scanner_task` runner and macOS launcher use `2`/`3`/`4`/`5`
for movement and `6` for pickup. The launcher can optionally enable pilot
controls `W`/`S`/`A`/`D` for movement; pickup remains `6`. Correct target-card
selection automatically completes the active instruction and reveals the next
one. The scanner run uses an eight-block palindrome (four forward conditions,
then their reverse), with one 30-second task period per block. It begins and
ends with 20 seconds of fixation and uses 10 seconds of fixation between the
seven block transitions, for a total duration of 350 seconds (5:50).
At every block boundary, the active unfinished card is discarded. The new
block starts with the next card–instruction pair in the shuffled sequence after
any cards that were completed during the preceding block. It also starts at a
new randomized safe position and heading on the same map. The eight starts are
distinct within a run and exclude cards, landmarks, blocked cells, and isolated
map regions. Randomization is reproducibly seeded by participant ID, run number,
map, and block number.
The Mac launcher also accepts a display number: `1` uses the primary display
and `2` normally uses the first extended monitor. All task presentation windows
are placed on the selected display.
After the display choice, select window layout `1` for maximum non-fullscreen,
`2` for the upper two-thirds of the monitor, or `3` for a centered window at
50% of the monitor's width and height.

Install the package from the repo root before running the server or driver:

```bash
python -m pip install -e .
```

For laptop testing outside the scanner, use `--not-in-scanner` so the startup screen accepts any key instead of waiting for `=`.

```bash
# Terminal 1: start the local game server
python -m cb2game.server.main --config_filepath=cb2fmri.yaml

# Terminal 2: run a Mac laptop test
python -m cb2game.fmri.main 1 1 A 3 1 --behavioral --not-in-scanner --materials-dir ~/cb2main-old/materials

# Optional: enable ratings and buttonbox practice
python -m cb2game.fmri.main 1 1 A 3 1 --behavioral --not-in-scanner --ratings --test-button-box
```

The experiment driver uses pygame 2.1.2, which can cause problems on ARM Macs. The game will still run properly with pygame 2.1.3. If running the experiment causes an error, try installing the pynput package independently with the following command:
```bash
pip install pynput
```

On the CLiMB Lab machine where cb2 is already installed, run the following commands in order to start the experiment with the buttonbox test:
```bash
conda activate cb2
python -m cb2game.server.main --config_filepath=cb2fmri.yaml

# in a separate terminal window
conda activate cb2
python -m cb2game.fmri.main 1 1 A 3 1 --behavioral --materials-dir ~/cb2main-old/materials
# before resampling, we are testing using the old repo's materials sample
```
