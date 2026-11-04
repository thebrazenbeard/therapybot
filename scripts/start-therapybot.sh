#!/usr/bin/env sh
set -eu
APP_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
APP_PYTHON="$APP_ROOT/.venv/bin/python"
if [ ! -x "$APP_PYTHON" ]; then
  echo 'Missing .venv. Run: python3 -m venv .venv && .venv/bin/python -m pip install -e .' >&2
  exit 1
fi
exec "$APP_PYTHON" -m therapybot "$@"
