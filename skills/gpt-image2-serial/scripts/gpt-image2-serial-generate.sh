#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PWD}"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  exec python3 "${SCRIPT_DIR}/generate.py" --help
fi

if [[ -f "${PROJECT_ROOT}/.env.image" ]]; then
  set -a
  source "${PROJECT_ROOT}/.env.image"
  set +a
fi

export OPENAI_IMAGE_API_KEY="${OPENAI_IMAGE_API_KEY:-${OPENAI_API_KEY:-}}"
export OPENAI_IMAGE_BASE_URL="${OPENAI_IMAGE_BASE_URL:-${OPENAI_BASE_URL:-https://api.openai.com/v1}}"

if [[ -z "${OPENAI_IMAGE_API_KEY}" ]]; then
  cat >&2 <<'EOF'
Missing image API key.

Set one of these before running:
  export OPENAI_IMAGE_API_KEY=your-key
  export OPENAI_IMAGE_BASE_URL=https://api.openai.com/v1   # optional

Or create a project-local .env.image file with:
  OPENAI_IMAGE_API_KEY=your-key
  OPENAI_IMAGE_BASE_URL=https://api.openai.com/v1   # optional
EOF
  exit 1
fi

exec python3 "${SCRIPT_DIR}/generate.py" "$@"
