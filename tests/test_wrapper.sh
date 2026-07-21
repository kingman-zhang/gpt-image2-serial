#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_SKILL_DIR="${ROOT_DIR}/skills/gpt-image2-serial"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "${haystack}" != *"${needle}"* ]]; then
    fail "expected to find '${needle}' in '${haystack}'"
  fi
}

assert_file_contains() {
  local file="$1"
  local needle="$2"
  if ! grep -Fq -- "${needle}" "${file}"; then
    fail "expected '${file}' to contain '${needle}'"
  fi
}

make_fixture() {
  local stub_client="${1:-1}"
  FIXTURE_DIR="$(mktemp -d)"
  export FIXTURE_DIR
  cp -R "${SOURCE_SKILL_DIR}" "${FIXTURE_DIR}/skill"
  CAPTURE_FILE="${FIXTURE_DIR}/capture.txt"
  export CAPTURE_FILE
  if [[ "${stub_client}" == "1" ]]; then
    python3 - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["FIXTURE_DIR"]) / "skill" / "scripts" / "generate.py"
capture = os.environ["CAPTURE_FILE"]
path.write_text(
    "#!/usr/bin/env python3\n"
    "import json\n"
    "import os\n"
    "import sys\n"
    "from pathlib import Path\n"
    f"capture = Path({capture!r})\n"
    "capture.write_text(json.dumps({\n"
    "    'argv': sys.argv[1:],\n"
    "    'key': os.environ.get('OPENAI_IMAGE_API_KEY') or os.environ.get('OPENAI_API_KEY', ''),\n"
    "    'base_url': os.environ.get('OPENAI_IMAGE_BASE_URL') or os.environ.get('OPENAI_BASE_URL', ''),\n"
    "}, indent=2))\n"
    "raise SystemExit(0)\n",
    encoding="utf-8",
)
PY
  fi
  WRAPPER="${FIXTURE_DIR}/skill/scripts/gpt-image2-serial-generate.sh"
  PROJECT_DIR="${FIXTURE_DIR}/project"
  HOME_DIR="${FIXTURE_DIR}/home"
  mkdir -p "${PROJECT_DIR}" "${HOME_DIR}"
}

run_wrapper() {
  local stdout_file="${FIXTURE_DIR}/stdout.txt"
  local stderr_file="${FIXTURE_DIR}/stderr.txt"
  set +e
  (
    cd "${PROJECT_DIR}"
    env -i PATH="${PATH}" HOME="${HOME_DIR}" "$@"
  ) >"${stdout_file}" 2>"${stderr_file}"
  STATUS=$?
  set -e
  STDOUT="$(cat "${stdout_file}")"
  STDERR="$(cat "${stderr_file}")"
}

cleanup_fixture() {
  rm -rf "${FIXTURE_DIR}"
}

test_missing_key() {
  make_fixture 0
  trap cleanup_fixture RETURN
  run_wrapper bash "${WRAPPER}" --out "${PROJECT_DIR}/out.png" --prompt "hello"
  [[ ${STATUS} -ne 0 ]] || fail "missing key should fail"
  assert_contains "${STDERR}" "configure.py"
  assert_contains "${STDERR}" ".config/gpt-image2-serial/env"
  assert_contains "${STDERR}" "Do not paste"
  [[ ! -f "${CAPTURE_FILE}" ]] || fail "client should not run without a key"
  trap - RETURN
  cleanup_fixture
}

test_preferred_env_vars() {
  make_fixture
  trap cleanup_fixture RETURN
  run_wrapper env OPENAI_IMAGE_API_KEY="test-image-key" OPENAI_IMAGE_BASE_URL="https://example.test/v1" bash "${WRAPPER}" --out "${PROJECT_DIR}/out.png" --prompt "hello"
  [[ ${STATUS} -eq 0 ]] || fail "preferred env vars should succeed"
  assert_file_contains "${CAPTURE_FILE}" "\"key\": \"test-image-key\""
  assert_file_contains "${CAPTURE_FILE}" "\"base_url\": \"https://example.test/v1\""
  assert_file_contains "${CAPTURE_FILE}" "\"argv\": ["
  trap - RETURN
  cleanup_fixture
}

test_fallback_env_vars() {
  make_fixture
  trap cleanup_fixture RETURN
  run_wrapper env OPENAI_API_KEY="fallback-key" OPENAI_BASE_URL="https://fallback.test/v1" bash "${WRAPPER}" --out "${PROJECT_DIR}/out.png" --prompt "hello"
  [[ ${STATUS} -eq 0 ]] || fail "fallback env vars should succeed"
  assert_file_contains "${CAPTURE_FILE}" "\"key\": \"fallback-key\""
  assert_file_contains "${CAPTURE_FILE}" "\"base_url\": \"https://fallback.test/v1\""
  trap - RETURN
  cleanup_fixture
}

test_dotenv_is_not_sourced_as_shell_code() {
  make_fixture 0
  trap cleanup_fixture RETURN
  cat > "${PROJECT_DIR}/.env.image" <<'EOF'
OPENAI_IMAGE_API_KEY=$(touch SHOULD_NOT_EXIST)
EOF
  run_wrapper bash "${WRAPPER}" --out "${PROJECT_DIR}/out.png" --prompt "hello"
  [[ ${STATUS} -ne 0 ]] || fail "unsafe dotenv should be rejected"
  assert_contains "${STDERR}" "unsafe"
  [[ ! -e "${PROJECT_DIR}/SHOULD_NOT_EXIST" ]] || fail "wrapper executed dotenv shell content"
  trap - RETURN
  cleanup_fixture
}

test_preferred_wins() {
  make_fixture
  trap cleanup_fixture RETURN
  run_wrapper env OPENAI_IMAGE_API_KEY="preferred-key" OPENAI_API_KEY="fallback-key" OPENAI_IMAGE_BASE_URL="https://preferred.test/v1" OPENAI_BASE_URL="https://fallback.test/v1" bash "${WRAPPER}" --out "${PROJECT_DIR}/out.png" --prompt "hello"
  [[ ${STATUS} -eq 0 ]] || fail "preferred vars should win"
  assert_file_contains "${CAPTURE_FILE}" "\"key\": \"preferred-key\""
  assert_file_contains "${CAPTURE_FILE}" "\"base_url\": \"https://preferred.test/v1\""
  trap - RETURN
  cleanup_fixture
}

test_help() {
  make_fixture 0
  trap cleanup_fixture RETURN
  run_wrapper bash "${WRAPPER}" --help
  [[ ${STATUS} -eq 0 ]] || fail "--help should succeed"
  assert_contains "${STDOUT}${STDERR}" "Generate one image"
  [[ ! -f "${CAPTURE_FILE}" ]] || fail "help should not invoke the client"
  trap - RETURN
  cleanup_fixture
}

test_missing_key
test_preferred_env_vars
test_fallback_env_vars
test_dotenv_is_not_sourced_as_shell_code
test_preferred_wins
test_help

echo "wrapper tests passed"
