import io
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "gpt-image2-serial"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

import configure


class ConfigureTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.home = Path(self.tempdir.name) / "home"
        self.home.mkdir()
        self.path = self.home / ".config" / "gpt-image2-serial" / "env"

    def test_wizard_writes_default_url_with_mode_0600(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        status = configure.run(
            home=self.home,
            input_fn=lambda prompt: "",
            secret_fn=lambda prompt: "wizard-secret",
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(status, 0)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertIn(
            "OPENAI_IMAGE_BASE_URL=https://api.openai.com/v1",
            self.path.read_text(encoding="utf-8"),
        )
        self.assertNotIn("wizard-secret", stdout.getvalue() + stderr.getvalue())

    def test_wizard_reprompts_after_empty_key(self):
        secrets = iter(("", "wizard-secret"))

        status = configure.run(
            home=self.home,
            input_fn=lambda prompt: "",
            secret_fn=lambda prompt: next(secrets),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )

        self.assertEqual(status, 0)
        self.assertIn(
            "OPENAI_IMAGE_API_KEY=wizard-secret",
            self.path.read_text(encoding="utf-8"),
        )

    def test_wizard_rejects_invalid_base_url_without_writing(self):
        stderr = io.StringIO()

        status = configure.run(
            home=self.home,
            input_fn=lambda prompt: "ftp://example.test",
            secret_fn=lambda prompt: "wizard-secret",
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(status, 0)
        self.assertIn("http", stderr.getvalue().lower())
        self.assertNotIn("wizard-secret", stderr.getvalue())
        self.assertFalse(self.path.exists())

    def test_existing_config_is_not_overwritten_when_user_declines(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"original")

        status = configure.run(
            home=self.home,
            input_fn=lambda prompt: "n",
            secret_fn=lambda prompt: self.fail("secret prompt must not run"),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )

        self.assertEqual(status, 0)
        self.assertEqual(self.path.read_bytes(), b"original")

    def test_existing_config_is_replaced_when_user_confirms(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"original")
        answers = iter(("yes", "https://replacement.test/v1"))

        stdout = io.StringIO()
        stderr = io.StringIO()
        status = configure.run(
            home=self.home,
            input_fn=lambda prompt: next(answers),
            secret_fn=lambda prompt: "replacement-secret",
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(status, 0)
        self.assertIn(
            "OPENAI_IMAGE_API_KEY=replacement-secret",
            self.path.read_text(encoding="utf-8"),
        )
        self.assertNotIn("replacement-secret", stdout.getvalue() + stderr.getvalue())

    def test_non_interactive_terminal_fails_without_prompting(self):
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
        self.assertIn("python3", result.stderr)
        self.assertIn(str(SCRIPT_DIR / "configure.py"), result.stderr)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
