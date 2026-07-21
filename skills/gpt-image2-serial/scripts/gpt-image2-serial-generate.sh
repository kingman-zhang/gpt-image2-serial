#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  exec python3 "${SCRIPT_DIR}/generate.py" --help
fi

exec python3 "${SCRIPT_DIR}/generate.py" "$@"
