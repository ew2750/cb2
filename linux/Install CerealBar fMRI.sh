#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="${0%/*}"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "Installing CerealBar fMRI locally..."

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH."
  exit 1
fi

PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! "$PYTHON_BIN" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
then
  echo "Python 3.9 or newer is required."
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e "$PROJECT_DIR"

if [[ ! -f "$PROJECT_DIR/src/cb2game/server/www/WebGL/index.html" ]]; then
  echo "The bundled Unity client is missing; downloading the published client..."
  "$VENV_DIR/bin/python" -m cb2game.server.fetch_client
fi

echo
echo "Installation complete. Run linux/Run CerealBar fMRI.sh."
