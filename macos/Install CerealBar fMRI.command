#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=${0:A:h}
PROJECT_DIR=${SCRIPT_DIR:h}
VENV_DIR="$PROJECT_DIR/.venv"

echo "Installing CerealBar fMRI locally..."
PYTHON_BIN="/usr/bin/python3"
if [[ ! -x "$PYTHON_BIN" ]] || \
   [[ "$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.9" ]]; then
  echo "The macOS system Python 3.9 installation is required."
  read "?Press Return to close."
  exit 1
fi

# Older CB2 binary dependencies require Python 3.9. Preserve a partial
# environment made by an earlier installer instead of deleting it.
if [[ -x "$VENV_DIR/bin/python" ]]; then
  VENV_VERSION=$("$VENV_DIR/bin/python" -c \
    'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  if [[ "$VENV_VERSION" != "3.9" ]]; then
    BACKUP_DIR="$PROJECT_DIR/.venv-incompatible-$VENV_VERSION-$(date +%Y%m%d-%H%M%S)"
    echo "Preserving incompatible Python $VENV_VERSION environment at:"
    echo "$BACKUP_DIR"
    mv "$VENV_DIR" "$BACKUP_DIR"
  fi
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e "$PROJECT_DIR"

if [[ ! -f "$PROJECT_DIR/src/cb2game/server/www/WebGL/index.html" ]]; then
  echo "The bundled Unity client is missing; downloading the published client..."
  "$VENV_DIR/bin/python" -m cb2game.server.fetch_client
fi

echo
echo "Installation complete. Double-click 'Run CerealBar fMRI.command'."
read "?Press Return to close."
