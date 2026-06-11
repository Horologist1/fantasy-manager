#!/usr/bin/env bash
# Fantasy Manager Devkit launcher (Linux/macOS).
# Double-click or run from a terminal. Starts a local server and opens
# the default browser. Press Ctrl+C to stop.

set -e
cd "$(dirname "$0")"
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required but was not found on PATH."
  echo "Install Node 18+ from https://nodejs.org/ and try again."
  exit 1
fi
exec node serve.mjs
