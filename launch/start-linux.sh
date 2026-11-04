#!/usr/bin/env sh
# Local runtime only. Dependency installation is explicit and one-time.
set -eu
INVOCATION_PWD=$(pwd -P)
cd "$(dirname "$0")/.."

MODE=run
WHEELS=
case "${1-}" in
  --setup)
    MODE=setup
    shift
    ;;
  --setup-offline)
    MODE=setup-offline
    shift
    if [ "$#" -ne 1 ] || [ -z "$1" ]; then
      echo "Supply an existing local wheel directory: --setup-offline PATH" >&2
      exit 2
    fi
    case "$1" in
      /*) WHEELS=$1 ;;
      *) WHEELS=$INVOCATION_PWD/$1 ;;
    esac
    if [ ! -d "$WHEELS" ]; then
      echo "Local wheel directory does not exist: --setup-offline PATH" >&2
      exit 2
    fi
    WHEELS=$(CDPATH= cd "$WHEELS" && pwd -P)
    shift
    ;;
  --check)
    MODE=check
    shift
    ;;
esac

if [ "$MODE" != run ] && [ "$#" -ne 0 ]; then
  echo "Setup and check modes do not accept application arguments" >&2
  exit 2
fi

if [ "$MODE" = setup ] || [ "$MODE" = setup-offline ]; then
  if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
  fi
  if [ "$MODE" = setup-offline ]; then
    # Never contact a package index or download model weights.
    .venv/bin/python -m pip --isolated install --no-index --find-links "$WHEELS" -r requirements.txt
  else
    echo "One-time setup may contact the Python package index; no model weights are downloaded." >&2
    .venv/bin/python -m pip install -r requirements.txt
  fi
fi

if [ ! -x .venv/bin/python ]; then
  echo "TherapyBot Python environment missing. Run --setup once (may use PyPI), or --setup-offline PATH with local wheels." >&2
  exit 2
fi

.venv/bin/python launch/preflight.py
if [ "$MODE" != run ]; then
  echo "TherapyBot local Python dependencies are ready. Model-server connectivity was not tested."
  exit 0
fi
exec .venv/bin/python -m therapybot "$@"
