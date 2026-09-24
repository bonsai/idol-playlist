#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v aw >/dev/null 2>&1; then
  exec aw "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m app.cli "$@"
fi

echo "error: aw and python3 are not installed" >&2
exit 127
