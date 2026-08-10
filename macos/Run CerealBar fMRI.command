#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
PROJECT_DIR=${SCRIPT_DIR:h}
PYTHON="$PROJECT_DIR/.venv/bin/python"
DATA_DIR="$PROJECT_DIR/data"
OUTPUT_DIR="$DATA_DIR/events"
SERVER_DATA_DIR="$DATA_DIR/server"

if [[ ! -x "$PYTHON" ]]; then
  echo "Please run 'Install CerealBar fMRI.command' first."
  read "?Press Return to close."
  exit 1
fi

read "SUBJECT_ID?Participant ID: "
read "RUN_NUMBER?Run number: "
read "RUN_SET?Run set (A-H): "
read "TEMPLATE?Condition template (1-4, blank = counterbalance by run): "
read "PILOT_WASD?Enable W/A/S/D pilot controls? (y/N): "
read "DISPLAY_NUMBER?Display number (1=main, 2=extended; blank=1): "
DISPLAY_NUMBER=${DISPLAY_NUMBER:-1}
echo "Window layout:"
echo "  1 = maximum size without fullscreen"
echo "  2 = upper two-thirds of the selected screen"
echo "  3 = centered at 50% of the selected screen"
read "WINDOW_LAYOUT?Choose window layout (1-3; blank=1): "
WINDOW_LAYOUT=${WINDOW_LAYOUT:-1}

mkdir -p "$OUTPUT_DIR" "$SERVER_DATA_DIR"
SERVER_LOG="$DATA_DIR/server.log"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$PROJECT_DIR"
CB2_BIND_HOST=127.0.0.1 "$PYTHON" -m cb2game.server.main \
  --config_filepath="$PROJECT_DIR/cb2fmri.yaml" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

echo "Starting the local game..."
SERVER_READY=0
for attempt in {1..120}; do
  if curl --silent --fail http://127.0.0.1:8080/data/config >/dev/null; then
    SERVER_READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "The local game could not start. See $SERVER_LOG"
    read "?Press Return to close."
    exit 1
  fi
  sleep 0.25
done
if [[ "$SERVER_READY" -ne 1 ]]; then
  echo "The local game did not become ready. See $SERVER_LOG"
  read "?Press Return to close."
  exit 1
fi

ARGS=(
  "$SUBJECT_ID" "$RUN_NUMBER" "$RUN_SET" 3 1
  --output-dir "$OUTPUT_DIR"
  --host http://127.0.0.1:8080
  --browser chrome
  --display-number "$DISPLAY_NUMBER"
  --window-layout "$WINDOW_LAYOUT"
)
if [[ -n "$TEMPLATE" ]]; then
  ARGS+=(--condition-template "$TEMPLATE")
fi
if [[ "${PILOT_WASD:l}" == "y" || "${PILOT_WASD:l}" == "yes" ]]; then
  ARGS+=(--pilot-wasd)
fi

"$PYTHON" -m cb2game.fmri.scanner_task "${ARGS[@]}"

echo
echo "Run complete. Event file saved in $OUTPUT_DIR"
read "?Press Return to close."
