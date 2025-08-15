#!/usr/bin/env bash
set -euo pipefail

# Create and install with uv in an isolated environment
# Requires: curl

PROJECT_ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Project root directory: $PROJECT_ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (Python package manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$HOME/.uv/bin:$PATH"
fi

echo "Python interpreter: $(python3 -V || true)"

# Create a local virtualenv managed by uv
echo "Creating .venv using uv..."
uv venv --seed "$PROJECT_ROOT_DIR/.venv"
source "$PROJECT_ROOT_DIR/.venv/bin/activate"

echo "Installing requirements..."
uv pip install --upgrade pip
uv pip install -r "$PROJECT_ROOT_DIR/requirements.txt"

echo "Done. To activate later, run:"
echo "  source $PROJECT_ROOT_DIR/.venv/bin/activate"

