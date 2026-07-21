# GPT Image 2 Serial Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a portable, credential-safe `gpt-image2-serial` skill with a standalone Python client for OpenAI-compatible image APIs.

**Architecture:** Keep repository documentation at the root and the installable package under `skills/gpt-image2-serial`. A small Bash wrapper loads project configuration and delegates one blocking request to a Python standard-library client; tests exercise the client against local HTTP servers without paid API calls.

**Tech Stack:** Bash, Python 3 standard library (`argparse`, `urllib`, `json`, `base64`, `tempfile`, `unittest`), Markdown, YAML.

---

## File Map

- `skills/gpt-image2-serial/scripts/generate.py`: Validate configuration, call the OpenAI-compatible endpoint, decode the response, and atomically write one image.
- `skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh`: Load `.env.image`, map preferred/fallback variables, and invoke the bundled client.
- `tests/test_generate.py`: Local HTTP-server coverage for success and failure behavior.
- `tests/test_wrapper.sh`: Shell-level configuration and argument checks.
- `skills/gpt-image2-serial/SKILL.md`: Portable agent workflow and failure guidance.
- `skills/gpt-image2-serial/agents/openai.yaml`: Codex UI metadata.
- `.env.image.example`: Safe configuration template.
- `.gitignore`: Secret and generated-file exclusions.
- `README.md`: GitHub installation and usage instructions.
- `LICENSE`: Repository license.

### Task 1: Build the Standalone HTTP Client

**Files:**
- Create: `tests/test_generate.py`
- Create: `skills/gpt-image2-serial/scripts/generate.py`

- [ ] **Step 1: Write failing client tests**

Create a `unittest` suite with an in-process `ThreadingHTTPServer`. Its handler must capture the request path, authorization header, and JSON body, then return selectable fixtures. Cover these exact cases:

```python
def test_base64_response_writes_image_atomically(self): ...
def test_url_response_downloads_image(self): ...
def test_base_url_trailing_slash_is_normalized(self): ...
def test_existing_output_is_rejected(self): ...
def test_401_hides_api_key(self): ...
def test_429_recommends_serial_retry(self): ...
def test_malformed_response_leaves_no_output(self): ...
```

Invoke the client as a subprocess so tests cover its CLI and stderr. For success, assert the request targets `/v1/images/generations`, sends `Bearer test-secret`, contains the requested model/prompt/size/quality/output format, exits `0`, and writes the expected bytes. For failures, assert a nonzero exit, an actionable message, absence of `test-secret` in output, and no destination file.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m unittest tests/test_generate.py -v
```

Expected: FAIL because `skills/gpt-image2-serial/scripts/generate.py` does not exist.

- [ ] **Step 3: Implement the minimal client**

Implement these boundaries in `generate.py`:

```python
def build_generation_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/images/generations"

def request_json(url: str, api_key: str, payload: dict[str, object]) -> dict[str, object]:
    ...

def extract_image(response: dict[str, object], api_key: str) -> bytes:
    ...

def atomic_write(path: Path, content: bytes) -> None:
    ...

def main(argv: list[str] | None = None) -> int:
    ...
```

Use `urllib.request.Request` with JSON bytes and `Authorization: Bearer ...`. Request `response_format: b64_json`; accept either `data[0].b64_json` or `data[0].url`. Download returned URLs without forwarding the API key to a different host. Use `tempfile.NamedTemporaryFile(delete=False, dir=destination.parent)` followed by `os.replace`, deleting the temporary file on failure. Map HTTP `401/403`, `429`, TLS/network, invalid JSON, invalid Base64, and missing image data to concise stderr messages and exit `1`.

- [ ] **Step 4: Run client tests to verify they pass**

Run:

```bash
python3 -m unittest tests/test_generate.py -v
python3 -m py_compile skills/gpt-image2-serial/scripts/generate.py
```

Expected: seven tests pass and compilation exits `0`.

- [ ] **Step 5: Commit the client slice**

```bash
git add tests/test_generate.py skills/gpt-image2-serial/scripts/generate.py
git commit -m "feat: add portable image generation client"
```

### Task 2: Add the Configuration Wrapper

**Files:**
- Create: `tests/test_wrapper.sh`
- Create: `skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh`

- [ ] **Step 1: Write failing wrapper tests**

Create a temporary project and stub `generate.py` by copying the skill to the temporary directory. Test:

```bash
# Missing key exits nonzero and mentions OPENAI_IMAGE_API_KEY plus .env.image.
# OPENAI_IMAGE_API_KEY and OPENAI_IMAGE_BASE_URL are passed to generate.py.
# OPENAI_API_KEY and OPENAI_BASE_URL work as fallbacks.
# Values from $PWD/.env.image are loaded.
# Preferred variables win over fallback variables.
# --help exits zero without requiring a key.
```

Replace the copied Python client in the test fixture with a stub that writes its environment and arguments to a capture file. Never write a real key into the repository; use `test-image-key` only inside the temporary directory.

- [ ] **Step 2: Run wrapper tests to verify they fail**

Run:

```bash
bash tests/test_wrapper.sh
```

Expected: FAIL because the wrapper does not exist.

- [ ] **Step 3: Implement the wrapper**

Use the caller's initial `$PWD` as `PROJECT_ROOT`, resolve `generate.py` relative to `BASH_SOURCE[0]`, and load `$PROJECT_ROOT/.env.image` with `set -a; source ...; set +a`. Export normalized client variables:

```bash
export OPENAI_IMAGE_API_KEY="${OPENAI_IMAGE_API_KEY:-${OPENAI_API_KEY:-}}"
export OPENAI_IMAGE_BASE_URL="${OPENAI_IMAGE_BASE_URL:-${OPENAI_BASE_URL:-https://api.openai.com/v1}}"
```

When the key is empty, print both setup alternatives and exit before invoking Python. Delegate all CLI flags unchanged with:

```bash
exec python3 "${SCRIPT_DIR}/generate.py" "$@"
```

- [ ] **Step 4: Verify wrapper behavior**

Run:

```bash
bash -n skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh
bash tests/test_wrapper.sh
```

Expected: syntax check exits `0` and all wrapper assertions pass.

- [ ] **Step 5: Commit the wrapper slice**

```bash
git add tests/test_wrapper.sh skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh
git commit -m "feat: add portable image generation wrapper"
```

### Task 3: Package the Agent Skill

**Files:**
- Create: `skills/gpt-image2-serial/SKILL.md`
- Create: `skills/gpt-image2-serial/agents/openai.yaml`

- [ ] **Step 1: Write the portable skill instructions**

Use frontmatter containing only `name` and `description`. The description must trigger for GPT Image 2, OpenAI-compatible image generation, concurrency-limit failures, and reliable serial generation. The body must instruct the agent to:

```text
1. Check OPENAI_IMAGE_API_KEY or OPENAI_API_KEY without displaying its value.
2. Ask the user to configure a key when neither is present.
3. Invoke scripts/gpt-image2-serial-generate.sh for exactly one output.
4. Wait for completion before issuing another invocation.
5. Verify the output file and never overwrite an existing file implicitly.
```

Retain actionable handling for `429` and proxy/TLS record-layer failures. Remove all references to `~/.codex/skills/.system/imagegen` and machine-specific proxy assumptions.

- [ ] **Step 2: Generate UI metadata**

Run the skill creator's generator with:

```bash
python3 /Users/zhangjianwen/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py \
  skills/gpt-image2-serial \
  --interface 'display_name=GPT Image 2 Serial' \
  --interface 'short_description=Generate GPT Image 2 assets reliably, one at a time' \
  --interface 'default_prompt=Use $gpt-image2-serial to generate one project image safely.'
```

Expected: `agents/openai.yaml` contains only quoted interface strings and its default prompt names `$gpt-image2-serial`.

- [ ] **Step 3: Validate the skill package**

Run:

```bash
python3 /Users/zhangjianwen/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/gpt-image2-serial
```

Expected: `Skill is valid!`

- [ ] **Step 4: Commit the skill package**

```bash
git add skills/gpt-image2-serial/SKILL.md skills/gpt-image2-serial/agents/openai.yaml
git commit -m "feat: package gpt image serial skill"
```

### Task 4: Add Safe Public Installation Documentation

**Files:**
- Create: `.env.image.example`
- Create: `.gitignore`
- Create: `README.md`
- Create: `LICENSE`

- [ ] **Step 1: Add configuration safeguards**

Create `.env.image.example`:

```dotenv
# Required. Never commit your real key.
OPENAI_IMAGE_API_KEY=

# Optional. Defaults to https://api.openai.com/v1
OPENAI_IMAGE_BASE_URL=
```

Create `.gitignore`:

```gitignore
.DS_Store
.env.image
__pycache__/
*.py[cod]
```

- [ ] **Step 2: Add README installation and usage**

Document one-command installation using a repository placeholder:

```bash
npx skills add <github-owner>/gpt-image2-serial
```

Also document manual copies of `skills/gpt-image2-serial` to `${CODEX_HOME:-~/.codex}/skills/` and `~/.claude/skills/`, Python 3 prerequisites, environment setup, `.env.image` setup, and one invocation example. State that the placeholder must be replaced after the GitHub remote is known and warn against committing credentials.

- [ ] **Step 3: Add a license**

Add the MIT License with copyright year `2026` and the repository owner's name if it is discoverable from Git configuration; otherwise use `gpt-image2-serial contributors`.

- [ ] **Step 4: Verify documentation consistency**

Run:

```bash
rg -n 'OPENAI_(IMAGE_)?(API_KEY|BASE_URL)|skills add|\.claude/skills|\.codex' README.md .env.image.example skills/gpt-image2-serial/SKILL.md
```

Expected: preferred and fallback variables are documented consistently, and both agent installation paths appear.

- [ ] **Step 5: Commit the public repository files**

```bash
git add .env.image.example .gitignore README.md LICENSE
git commit -m "docs: add installation and configuration guide"
```

### Task 5: Complete Repository Verification

**Files:**
- Modify only files found defective by verification.

- [ ] **Step 1: Run the complete offline suite**

```bash
python3 -m unittest tests/test_generate.py -v
bash tests/test_wrapper.sh
bash -n skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh
python3 -m py_compile skills/gpt-image2-serial/scripts/generate.py
python3 /Users/zhangjianwen/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/gpt-image2-serial
git diff --check
```

Expected: all tests pass, both syntax checks exit `0`, validation prints `Skill is valid!`, and `git diff --check` is silent.

- [ ] **Step 2: Scan for sensitive or machine-specific values**

```bash
rg -n --hidden -g '!.git/**' \
  '(sk-[A-Za-z0-9_-]{16,}|127\.0\.0\.1:7890|/Users/[^/]+|OPENAI_[A-Z_]+=[^[:space:]]+)' .
```

Expected: no real key, private endpoint, proxy address, or runtime machine path appears in published files. The design and plan may reference local tooling paths only as development commands and must not be included in the installable package.

- [ ] **Step 3: Inspect the final repository state**

```bash
git status --short
git log --oneline --decorate -5
find skills/gpt-image2-serial -maxdepth 3 -type f -print | sort
```

Expected: only intentionally uncommitted planning changes remain, recent commits correspond to the implementation slices, and the skill package contains `SKILL.md`, `agents/openai.yaml`, and two scripts.

- [ ] **Step 4: Defer live API verification**

Do not issue a paid request automatically. Report that offline mock coverage passed and ask for explicit approval before an optional live generation test using the user's configured environment.
