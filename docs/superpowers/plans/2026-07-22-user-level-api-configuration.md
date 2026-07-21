# User-Level API Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a secure terminal configuration wizard and a user-level API configuration file so a new user can configure the skill once without pasting secrets into chat.

**Architecture:** Add a focused `config.py` module for restricted dotenv parsing, precedence resolution, and secure atomic writes. `configure.py` owns interactive prompting, while `generate.py` resolves environment, project, and user configuration before contacting the API; the shell wrapper remains a thin launcher.

**Tech Stack:** Python 3 standard library, Bash, `unittest`, Markdown, Codex skill validator

---

## File Map

- Create `skills/gpt-image2-serial/scripts/config.py`: configuration paths, restricted dotenv parser, precedence resolution, and secure atomic writes.
- Create `skills/gpt-image2-serial/scripts/configure.py`: interactive hidden-input setup wizard.
- Modify `skills/gpt-image2-serial/scripts/generate.py`: resolve configuration through `config.py` and improve missing-configuration errors.
- Modify `skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh`: remove shell `source` behavior and delegate configuration to Python.
- Create `tests/test_config.py`: unit tests for parsing, precedence, and secure writes.
- Create `tests/test_configure.py`: subprocess tests for wizard success and refusal paths.
- Modify `tests/test_generate.py`: isolate tests from real user configuration and test missing-configuration guidance.
- Modify `tests/test_wrapper.sh`: verify the wrapper forwards arguments without sourcing executable dotenv content.
- Modify `skills/gpt-image2-serial/SKILL.md`: require the safe wizard when configuration is missing.
- Modify `skills/gpt-image2-serial/agents/openai.yaml`: align the default prompt with first-use configuration behavior if its current prompt becomes stale.
- Modify `README.md`: make user-level configuration the default Chinese onboarding path.
- Modify `README.en.md`: mirror the configuration flow in English.
- Modify `.env.image.example`: label it as an advanced project-level override.

### Task 1: Restricted Configuration Core

**Files:**
- Create: `skills/gpt-image2-serial/scripts/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for paths, parsing, precedence, and secure writes**

Create `tests/test_config.py` with tests that import `config.py` by inserting its script directory into `sys.path`. Cover these concrete cases:

```python
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "gpt-image2-serial" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.home = self.root / "home"
        self.project = self.root / "project"
        self.home.mkdir()
        self.project.mkdir()

    def test_user_config_path_uses_home(self):
        self.assertEqual(
            config.user_config_path(self.home),
            self.home / ".config" / "gpt-image2-serial" / "env",
        )

    def test_parse_dotenv_accepts_known_keys(self):
        path = self.project / ".env.image"
        path.write_text(
            "OPENAI_IMAGE_API_KEY=test-key\n"
            "OPENAI_IMAGE_BASE_URL=https://example.test/v1\n",
            encoding="utf-8",
        )
        self.assertEqual(
            config.read_dotenv(path),
            {
                "OPENAI_IMAGE_API_KEY": "test-key",
                "OPENAI_IMAGE_BASE_URL": "https://example.test/v1",
            },
        )

    def test_parse_dotenv_rejects_shell_syntax_and_unknown_keys(self):
        for content in ("OPENAI_IMAGE_API_KEY=$(whoami)\n", "OTHER_KEY=value\n"):
            path = self.project / ".env.image"
            path.write_text(content, encoding="utf-8")
            with self.subTest(content=content):
                with self.assertRaises(config.ConfigError):
                    config.read_dotenv(path)

    def test_resolution_order_is_environment_then_project_then_user(self):
        user_path = config.user_config_path(self.home)
        user_path.parent.mkdir(parents=True)
        user_path.write_text(
            "OPENAI_IMAGE_API_KEY=user-key\n"
            "OPENAI_IMAGE_BASE_URL=https://user.test/v1\n",
            encoding="utf-8",
        )
        (self.project / ".env.image").write_text(
            "OPENAI_IMAGE_API_KEY=project-key\n"
            "OPENAI_IMAGE_BASE_URL=https://project.test/v1\n",
            encoding="utf-8",
        )
        resolved = config.resolve_config(
            environ={"OPENAI_IMAGE_API_KEY": "env-key"},
            project_dir=self.project,
            home=self.home,
        )
        self.assertEqual(resolved.api_key, "env-key")
        self.assertEqual(resolved.base_url, "https://project.test/v1")

    def test_fallback_environment_names_are_supported(self):
        resolved = config.resolve_config(
            environ={
                "OPENAI_API_KEY": "fallback-key",
                "OPENAI_BASE_URL": "https://fallback.test/v1",
            },
            project_dir=self.project,
            home=self.home,
        )
        self.assertEqual(resolved.api_key, "fallback-key")
        self.assertEqual(resolved.base_url, "https://fallback.test/v1")

    def test_secure_write_creates_mode_0600_without_leaking_secret(self):
        path = config.user_config_path(self.home)
        config.write_user_config(path, "secret-key", "https://example.test/v1")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertIn("OPENAI_IMAGE_API_KEY=secret-key", path.read_text(encoding="utf-8"))
        self.assertEqual(list(path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_config.py -v
```

Expected: FAIL because `skills/gpt-image2-serial/scripts/config.py` does not exist.

- [ ] **Step 3: Implement the configuration module**

Create `config.py` with `ImageConfig`, an immutable dataclass containing `api_key: str | None` and `base_url: str`, plus `ConfigError(ValueError)`. Export these exact functions:

- `user_config_path(home: Path | None = None) -> Path`
- `read_dotenv(path: Path) -> dict[str, str]`
- `resolve_config(environ: Mapping[str, str] | None = None, project_dir: Path | None = None, home: Path | None = None) -> ImageConfig`
- `validate_base_url(value: str) -> str`
- `write_user_config(path: Path, api_key: str, base_url: str) -> None`

Implementation requirements:

- Accept only `OPENAI_IMAGE_API_KEY` and `OPENAI_IMAGE_BASE_URL` in dotenv files.
- Ignore blank lines and `#` comments.
- Accept unquoted values and matching single- or double-quoted values.
- Reject command substitutions, backticks, `export`, unknown keys, malformed lines, and multiline values with `ConfigError`.
- Resolve each field independently using preferred environment name, fallback environment name, project file, user file, then the default Base URL.
- Validate Base URL using `urllib.parse.urlparse`; require scheme `http` or `https` and a non-empty host.
- Create the parent directory with mode `0700` where supported.
- Write with `tempfile.NamedTemporaryFile`, `os.fchmod(handle.fileno(), 0o600)`, `os.replace`, and cleanup in `finally`.

- [ ] **Step 4: Run configuration tests**

Run:

```bash
python3 -m unittest tests/test_config.py -v
```

Expected: all `ConfigTests` pass.

- [ ] **Step 5: Commit the configuration core**

```bash
git add skills/gpt-image2-serial/scripts/config.py tests/test_config.py
git commit -m "feat: add secure image API configuration core"
```

### Task 2: Interactive Configuration Wizard

**Files:**
- Create: `skills/gpt-image2-serial/scripts/configure.py`
- Create: `tests/test_configure.py`

- [ ] **Step 1: Write failing subprocess tests for the wizard**

Create `tests/test_configure.py`. Import `configure.py` from `SCRIPT_DIR`, call its injectable `run()` function for interaction tests, and reserve a subprocess with `stdin=subprocess.DEVNULL` for the non-interactive CLI test. Use `io.StringIO` for captured streams and these concrete test bodies:

```python
def test_wizard_writes_default_url_with_mode_0600(self):
    stdout, stderr = io.StringIO(), io.StringIO()
    status = configure.run(
        home=self.home,
        input_fn=lambda prompt: "",
        secret_fn=lambda prompt: "wizard-secret",
        stdout=stdout,
        stderr=stderr,
    )
    path = self.home / ".config" / "gpt-image2-serial" / "env"
    self.assertEqual(status, 0)
    self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
    self.assertIn("OPENAI_IMAGE_BASE_URL=https://api.openai.com/v1", path.read_text())
    self.assertNotIn("wizard-secret", stdout.getvalue() + stderr.getvalue())

def test_wizard_rejects_empty_key_without_writing(self):
    status = configure.run(
        home=self.home,
        input_fn=lambda prompt: "",
        secret_fn=lambda prompt: "",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    self.assertNotEqual(status, 0)
    self.assertFalse((self.home / ".config" / "gpt-image2-serial" / "env").exists())

def test_wizard_rejects_invalid_base_url_without_writing(self):
    answers = iter(["ftp://example.test"])
    status = configure.run(
        home=self.home,
        input_fn=lambda prompt: next(answers),
        secret_fn=lambda prompt: "wizard-secret",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    self.assertNotEqual(status, 0)
    self.assertFalse((self.home / ".config" / "gpt-image2-serial" / "env").exists())

def test_existing_config_is_not_overwritten_when_user_declines(self):
    path = self.home / ".config" / "gpt-image2-serial" / "env"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"original")
    status = configure.run(
        home=self.home,
        input_fn=lambda prompt: "n",
        secret_fn=lambda prompt: self.fail("secret prompt must not run"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    self.assertEqual(status, 0)
    self.assertEqual(path.read_bytes(), b"original")

def test_non_interactive_terminal_fails_without_prompting_for_secret(self):
    env = os.environ.copy()
    env["HOME"] = str(self.home)
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "configure.py")],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env=env,
    )
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("interactive terminal", result.stderr.lower())
```

Use a sentinel secret in every test and assert it is absent from captured stdout and stderr.

- [ ] **Step 2: Run wizard tests and verify they fail**

```bash
python3 -m unittest tests/test_configure.py -v
```

Expected: FAIL because `configure.py` is absent.

- [ ] **Step 3: Implement the interactive wizard**

Create `configure.py` with the exact injectable signature `run(*, home: Path | None = None, input_fn: Callable[[str], str] = input, secret_fn: Callable[[str], str] = getpass.getpass, stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int`. Add `main() -> int` for the TTY check, and use `raise SystemExit(main())` in the CLI entry point.

The function must:

- Refuse to run when `sys.stdin.isatty()` is false in the normal CLI path.
- Display `user_config_path(home).expanduser()` before collecting input.
- Ask before replacing an existing file; accept only `y` or `yes` case-insensitively.
- Read the key only through `secret_fn`.
- Use the default Base URL when `input_fn` returns blank.
- Call `validate_base_url()` and `write_user_config()` from `config.py`.
- Print success and the path, never the key.

- [ ] **Step 4: Run wizard tests**

```bash
python3 -m unittest tests/test_configure.py -v
```

Expected: all wizard tests pass.

- [ ] **Step 5: Commit the wizard**

```bash
git add skills/gpt-image2-serial/scripts/configure.py tests/test_configure.py
git commit -m "feat: add safe image API setup wizard"
```

### Task 3: Integrate Configuration Into Generation

**Files:**
- Modify: `skills/gpt-image2-serial/scripts/generate.py`
- Modify: `skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh`
- Modify: `tests/test_generate.py`
- Modify: `tests/test_wrapper.sh`

- [ ] **Step 1: Add failing generation and wrapper tests**

Update `tests/test_generate.py` so `run_script()` starts from an environment that explicitly removes all four API variables and sets `HOME` to the test temporary directory before applying per-test overrides. Add:

```python
def test_user_config_is_loaded_when_environment_is_empty(self):
    config_path = Path(self.tempdir.name) / "home" / ".config" / "gpt-image2-serial" / "env"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "OPENAI_IMAGE_API_KEY=user-secret\n"
        f"OPENAI_IMAGE_BASE_URL={self.base_url}\n",
        encoding="utf-8",
    )
    result = self.run_script(env={}, home=config_path.parents[2])
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(FixtureHandler.records[0]["authorization"], "Bearer user-secret")

def test_missing_config_points_to_wizard_without_leaking(self):
    result = self.run_script(env={}, include_default_config=False)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("configure.py", result.stderr)
    self.assertIn(".config/gpt-image2-serial/env", result.stderr)
    self.assertIn("do not paste", result.stderr.lower())
```

Update `tests/test_wrapper.sh` with a malicious project dotenv fixture:

```bash
cat > "${PROJECT_DIR}/.env.image" <<'EOF'
OPENAI_IMAGE_API_KEY=$(touch SHOULD_NOT_EXIST)
EOF
run_wrapper bash "${WRAPPER}" --out "${PROJECT_DIR}/out.png" --prompt "hello"
[[ ! -e "${PROJECT_DIR}/SHOULD_NOT_EXIST" ]] || fail "wrapper executed dotenv shell content"
```

- [ ] **Step 2: Run focused tests and verify failure**

```bash
python3 -m unittest tests/test_generate.py -v
bash tests/test_wrapper.sh
```

Expected: new tests fail because `generate.py` does not load user configuration and the wrapper still sources `.env.image`.

- [ ] **Step 3: Integrate `resolve_config()` into `generate.py`**

Replace direct environment lookup with:

```python
try:
    image_config = resolve_config(project_dir=Path.cwd())
except ConfigError as exc:
    return fail(f"Invalid image API configuration: {exc}")

if not image_config.api_key:
    config_path = user_config_path().expanduser()
    configure_script = Path(__file__).with_name("configure.py")
    return fail(
        "Missing image API key.\n"
        f"User configuration: {config_path}\n"
        f"Run this setup wizard in a terminal: python3 {configure_script}\n"
        "Do not paste your API key into chat."
    )

api_key = image_config.api_key
base_url = image_config.base_url
```

Import the public functions and exception from the adjacent `config.py` module. Preserve existing HTTP error handling and output behavior.

- [ ] **Step 4: Make the shell wrapper a thin launcher**

Reduce the wrapper to strict mode, `SCRIPT_DIR`, optional `--help`, and:

```bash
exec python3 "${SCRIPT_DIR}/generate.py" "$@"
```

Do not `source` either project or user configuration.

- [ ] **Step 5: Run generation and wrapper tests**

```bash
python3 -m unittest tests/test_generate.py -v
bash tests/test_wrapper.sh
```

Expected: all tests pass; no real API request occurs.

- [ ] **Step 6: Commit generation integration**

```bash
git add skills/gpt-image2-serial/scripts/generate.py \
  skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh \
  tests/test_generate.py tests/test_wrapper.sh
git commit -m "feat: load user-level image API configuration"
```

### Task 4: Agent Instructions and Public Documentation

**Files:**
- Modify: `skills/gpt-image2-serial/SKILL.md`
- Modify: `skills/gpt-image2-serial/agents/openai.yaml`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `.env.image.example`

- [ ] **Step 1: Update `SKILL.md` first-use behavior**

Replace the missing-key workflow with explicit instructions to:

```text
检查环境变量、当前目录的 .env.image 和 ~/.config/gpt-image2-serial/env，
但不要读取或回显 key。如果缺少 key，告诉用户配置文件的完整路径，
并在可交互终端中运行 scripts/configure.py。不要要求用户把 key 发到聊天中。
配置成功后继续原来的出图请求，不要求用户重新描述任务。
```

Document the precedence order and the non-interactive fallback command. Keep `SKILL.md` concise and under 500 lines.

- [ ] **Step 2: Align `agents/openai.yaml`**

Inspect its `default_prompt`. If it implies immediate generation without configuration handling, change it to a concise Chinese prompt that asks the Agent to configure safely when necessary and then generate one image serially.

- [ ] **Step 3: Rewrite the Chinese configuration section**

In `README.md`:

- Make `~/.config/gpt-image2-serial/env` the default configuration.
- Show the Agent prompt: “请为 gpt-image2-serial 启动安全配置向导。不要让我把 API key 发到聊天里；请在终端隐藏输入并保存到用户级配置。”
- Show the manual wizard command using the installed skill path for Codex and Claude Code.
- Explain that the wizard displays the exact path and applies `0600` permissions.
- Move environment variables and project `.env.image` into an “高级配置” subsection.
- Explain how to update by rerunning the wizard and how to delete by removing the displayed user config file.
- Remove the default onboarding instruction that assumes `.env.image.example` exists in the current project.

- [ ] **Step 4: Mirror the flow in English**

Apply the same information architecture and safety guarantees in `README.en.md`, including a complete English Agent prompt and platform-specific wizard paths.

- [ ] **Step 5: Clarify `.env.image.example`**

Change its leading comment to state that it is an optional advanced per-project override and that the recommended setup is the user-level wizard. Keep all values empty or public defaults.

- [ ] **Step 6: Validate documentation and skill metadata**

```bash
python3 /Users/zhangjianwen/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/gpt-image2-serial
git diff --check
```

Expected: `Skill is valid!` and no whitespace errors.

- [ ] **Step 7: Commit documentation**

```bash
git add README.md README.en.md .env.image.example \
  skills/gpt-image2-serial/SKILL.md \
  skills/gpt-image2-serial/agents/openai.yaml
git commit -m "docs: guide users through secure API setup"
```

### Task 5: Full Verification

**Files:**
- Verify only; modify earlier files only if a test exposes a defect.

- [ ] **Step 1: Run the complete automated test suite**

```bash
python3 -m unittest tests/test_config.py tests/test_configure.py tests/test_generate.py -v
bash tests/test_wrapper.sh
```

Expected: all Python and wrapper tests pass.

- [ ] **Step 2: Validate the packaged skill**

```bash
python3 /Users/zhangjianwen/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/gpt-image2-serial
git diff --check
```

Expected: `Skill is valid!` and no whitespace errors.

- [ ] **Step 3: Perform a temporary-HOME smoke test**

Run the wizard and generation configuration checks only against a temporary HOME. Do not use a real API key:

```bash
TEMP_HOME="$(mktemp -d)"
HOME="${TEMP_HOME}" python3 skills/gpt-image2-serial/scripts/configure.py
```

At the prompt, enter a disposable sentinel such as `test-only-key` and accept the default URL. Then verify:

```bash
stat -f '%Lp %N' "${TEMP_HOME}/.config/gpt-image2-serial/env"
HOME="${TEMP_HOME}" python3 skills/gpt-image2-serial/scripts/generate.py \
  --out "${TEMP_HOME}/out.png" --prompt "test"
```

Expected: mode output begins with `600`; generation reaches the API and fails with an authentication or network error without printing `test-only-key`. Remove the temporary directory afterward.

- [ ] **Step 4: Check repository state**

```bash
git status --short --branch
git log -5 --oneline --decorate
```

Expected: only pre-existing untracked `assets/` remains; implementation commits are present and no implementation files are unstaged.
