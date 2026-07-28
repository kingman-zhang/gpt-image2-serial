# macOS System CA Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make HTTPS image generation work with python.org macOS installations whose configured OpenSSL CA file is missing.

**Architecture:** Add one SSL-context factory to the existing Python client. It keeps explicit and working default trust settings intact, selects `/etc/ssl/cert.pem` only for the affected macOS case, and supplies the resulting verified context to both HTTP request paths.

**Tech Stack:** Python 3 standard library, `ssl`, `urllib.request`, `unittest`, `unittest.mock`

---

### Task 1: Specify CA selection behavior

**Files:**
- Modify: `tests/test_generate.py`

- [ ] **Step 1: Load `generate.py` as a testable module**

Use `importlib.util.spec_from_file_location` so tests can call the SSL helper
without spawning the command-line client.

- [ ] **Step 2: Add a failing macOS fallback test**

Patch `sys.platform` to `darwin`, clear `SSL_CERT_FILE` and `SSL_CERT_DIR`, make
`ssl.get_default_verify_paths()` report no effective trust source, make only
`/etc/ssl/cert.pem` appear present, and assert:

```python
create_default_context.assert_called_once_with(cafile="/etc/ssl/cert.pem")
```

- [ ] **Step 3: Add preservation and platform boundary tests**

Assert the helper calls `ssl.create_default_context()` without a fallback when
an explicit certificate variable is set, a Python default CA source exists, or
the platform is not macOS.

- [ ] **Step 4: Run the focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_generate.SSLContextTests -v
```

Expected: failure because `create_ssl_context` does not exist.

### Task 2: Implement verified macOS CA fallback

**Files:**
- Modify: `skills/gpt-image2-serial/scripts/generate.py`
- Test: `tests/test_generate.py`

- [ ] **Step 1: Implement the minimal context factory**

Add `create_ssl_context()` that honors explicit certificate variables and
effective Python defaults, then selects `/etc/ssl/cert.pem` only on macOS when
those sources are unavailable.

- [ ] **Step 2: Pass one context through both request paths**

Change the relevant signatures to:

```python
def request_json(url, api_key, payload, ssl_context):
def download_image(url, ssl_context):
def extract_image(response, ssl_context):
```

Pass `context=ssl_context` to both `urllib.request.urlopen` calls. Create the
context once in `main()` and pass it through extraction.

- [ ] **Step 3: Run the focused tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_generate.SSLContextTests -v
```

Expected: all SSL context tests pass.

- [ ] **Step 4: Run the complete automated suite**

Run:

```bash
python3 -m unittest discover -s tests -v
bash tests/test_wrapper.sh
```

Expected: all Python and wrapper tests pass.

### Task 3: Verify the original failure end to end

**Files:**
- Create during verification only: `assets/proxy-global-test.png`

- [ ] **Step 1: Run one serial image generation**

Run the existing wrapper with the configured API, current proxy environment,
and a new output filename.

- [ ] **Step 2: Verify the output**

Confirm the command succeeds, the output exists, and its detected type is PNG.
Visually inspect the generated image.

- [ ] **Step 3: Review the final diff**

Run `git diff --check`, inspect the scoped diff, and confirm no API key or local
configuration was added.
