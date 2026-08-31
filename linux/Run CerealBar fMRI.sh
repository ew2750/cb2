#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="${0%/*}"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
DATA_DIR="$PROJECT_DIR/data"
OUTPUT_DIR="$DATA_DIR/events"
SERVER_DATA_DIR="$DATA_DIR/server"

if [[ ! -x "$PYTHON" ]]; then
  echo "Please run 'Install CerealBar fMRI.sh' first."
  exit 1
fi

echo "Task mode:"
echo "  1 = fMRI task (30s task; 10s/20s fixation)"
echo "  2 = practice (30s task; 3s instructional fixation)"
echo "  3 = test dry run (3s task; 1s/2s fixation)"
read -r -p "Choose task mode (1-3; blank=1): " MODE_CHOICE
case "${MODE_CHOICE:-1}" in
  1) TASK_MODE="fmri" ;;
  2) TASK_MODE="practice" ;;
  3) TASK_MODE="dry-run" ;;
  *)
    echo "Invalid task mode. Choose 1, 2, or 3."
    exit 1
    ;;
esac

if [[ "$TASK_MODE" == "fmri" ]]; then
  read -r -p "Participant ID: " SUBJECT_ID
  read -r -p "Session ID: " SESSION_ID
  if [[ -z "${SUBJECT_ID//[[:space:]]/}" || -z "${SESSION_ID//[[:space:]]/}" ]]; then
    echo "Participant ID and Session ID cannot be blank."
    exit 1
  fi

  read -r -p "Material set (1-10): " SET_NUMBER
  if [[ ! "$SET_NUMBER" =~ ^(10|[1-9])$ ]]; then
    echo "Invalid material set. Choose a number from 1 to 10."
    exit 1
  fi

  read -r -p "Run (1-8): " RUN_NUMBER
  if [[ ! "$RUN_NUMBER" =~ ^[1-8]$ ]]; then
    echo "Invalid run. Choose a number from 1 to 8."
    exit 1
  fi

  read -r -p "Display number (1=main, 2=extended; blank=1): " DISPLAY_NUMBER
  DISPLAY_NUMBER=${DISPLAY_NUMBER:-1}
  echo "Window layout:"
  echo "  1 = maximum size without fullscreen"
  echo "  2 = upper two-thirds of the selected screen"
  echo "  3 = centered at 50% of the selected screen"
  read -r -p "Choose window layout (1-3; blank=1): " WINDOW_LAYOUT
  WINDOW_LAYOUT=${WINDOW_LAYOUT:-1}
else
  SUBJECT_ID="$TASK_MODE"
  SESSION_ID="$TASK_MODE"
  SET_NUMBER="prac"
  RUN_NUMBER="prac"
  DISPLAY_NUMBER=1
  WINDOW_LAYOUT=1
  echo "Using practice materials, WASD controls, display 1, and layout 1."
fi

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
    exit 1
  fi
  sleep 0.25
done

if [[ "$SERVER_READY" -ne 1 ]]; then
  echo "The local game did not become ready. See $SERVER_LOG"
  exit 1
fi

ARGS=(
  "$SUBJECT_ID" "$SET_NUMBER" "$RUN_NUMBER"
  --session-id "$SESSION_ID"
  --output-dir "$OUTPUT_DIR"
  --host http://127.0.0.1:8080
  --browser chrome
  --mode "$TASK_MODE"
  --display-number "$DISPLAY_NUMBER"
  --window-layout "$WINDOW_LAYOUT"
)
if [[ "$TASK_MODE" != "fmri" ]]; then
  ARGS+=(--pilot-wasd)
fi

"$PYTHON" -m cb2game.fmri.scanner_task "${ARGS[@]}"

echo
echo "Run complete. Event file saved in $OUTPUT_DIR"
