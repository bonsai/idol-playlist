#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v aw >/dev/null 2>&1; then
  exec aw "$@"
fi

exec python -m app.cli "$@"
