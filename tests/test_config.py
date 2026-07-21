import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "gpt-image2-serial"
    / "scripts"
)
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

    def write_config(self, path, key, base_url):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"OPENAI_IMAGE_API_KEY={key}\n"
            f"OPENAI_IMAGE_BASE_URL={base_url}\n",
            encoding="utf-8",
        )

    def test_user_config_path_uses_home(self):
        self.assertEqual(
            config.user_config_path(self.home),
            self.home / ".config" / "gpt-image2-serial" / "env",
        )

    def test_read_dotenv_accepts_known_keys_and_quotes(self):
        path = self.project / ".env.image"
        path.write_text(
            "# project override\n"
            "OPENAI_IMAGE_API_KEY='test-key'\n"
            'OPENAI_IMAGE_BASE_URL="https://example.test/v1"\n',
            encoding="utf-8",
        )

        self.assertEqual(
            config.read_dotenv(path),
            {
                "OPENAI_IMAGE_API_KEY": "test-key",
                "OPENAI_IMAGE_BASE_URL": "https://example.test/v1",
            },
        )

    def test_read_dotenv_rejects_unknown_keys(self):
        path = self.project / ".env.image"
        path.write_text("OTHER_KEY=value\n", encoding="utf-8")

        with self.assertRaisesRegex(config.ConfigError, "unknown"):
            config.read_dotenv(path)

    def test_read_dotenv_rejects_shell_syntax(self):
        unsafe_values = ("$(whoami)", "`whoami`", "${HOME}")
        for value in unsafe_values:
            with self.subTest(value=value):
                path = self.project / ".env.image"
                path.write_text(
                    f"OPENAI_IMAGE_API_KEY={value}\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(config.ConfigError, "unsafe"):
                    config.read_dotenv(path)

    def test_read_dotenv_wraps_invalid_utf8(self):
        path = self.project / ".env.image"
        path.write_bytes(b"OPENAI_IMAGE_API_KEY=\xff\n")

        with self.assertRaisesRegex(config.ConfigError, "cannot read"):
            config.read_dotenv(path)

    def test_environment_fields_override_project_and_user_independently(self):
        self.write_config(
            config.user_config_path(self.home),
            "user-key",
            "https://user.test/v1",
        )
        self.write_config(
            self.project / ".env.image",
            "project-key",
            "https://project.test/v1",
        )

        resolved = config.resolve_config(
            environ={"OPENAI_IMAGE_API_KEY": "env-key"},
            project_dir=self.project,
            home=self.home,
        )

        self.assertEqual(resolved.api_key, "env-key")
        self.assertEqual(resolved.base_url, "https://project.test/v1")

    def test_project_fields_override_user_fields_independently(self):
        self.write_config(
            config.user_config_path(self.home),
            "user-key",
            "https://user.test/v1",
        )
        (self.project / ".env.image").write_text(
            "OPENAI_IMAGE_API_KEY=project-key\n",
            encoding="utf-8",
        )

        resolved = config.resolve_config(
            environ={},
            project_dir=self.project,
            home=self.home,
        )

        self.assertEqual(resolved.api_key, "project-key")
        self.assertEqual(resolved.base_url, "https://user.test/v1")

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

    def test_complete_environment_ignores_malformed_lower_priority_files(self):
        (self.project / ".env.image").write_text("OTHER_KEY=bad\n", encoding="utf-8")
        user_path = config.user_config_path(self.home)
        user_path.parent.mkdir(parents=True)
        user_path.write_text("OTHER_KEY=bad\n", encoding="utf-8")

        resolved = config.resolve_config(
            environ={
                "OPENAI_IMAGE_API_KEY": "environment-key",
                "OPENAI_IMAGE_BASE_URL": "https://environment.test/v1",
            },
            project_dir=self.project,
            home=self.home,
        )

        self.assertEqual(resolved.api_key, "environment-key")
        self.assertEqual(resolved.base_url, "https://environment.test/v1")

    def test_default_base_url_is_used_without_configuration(self):
        resolved = config.resolve_config(
            environ={},
            project_dir=self.project,
            home=self.home,
        )

        self.assertIsNone(resolved.api_key)
        self.assertEqual(resolved.base_url, "https://api.openai.com/v1")

    def test_validate_base_url_rejects_non_http_urls(self):
        for value in (
            "ftp://example.test",
            "example.test/v1",
            "https:///v1",
            "https://user@",
            "https://example.test:invalid",
            "https://example.test/\x00",
        ):
            with self.subTest(value=value):
                with self.assertRaises(config.ConfigError):
                    config.validate_base_url(value)

    def test_secure_write_creates_mode_0600_and_no_temp_file(self):
        path = config.user_config_path(self.home)

        config.write_user_config(path, "secret-key", "https://example.test/v1")

        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "OPENAI_IMAGE_API_KEY=secret-key\n"
            "OPENAI_IMAGE_BASE_URL=https://example.test/v1\n",
        )
        self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_secure_write_rejects_line_breaks_in_key(self):
        path = config.user_config_path(self.home)

        with self.assertRaises(config.ConfigError):
            config.write_user_config(
                path,
                "secret\nOPENAI_IMAGE_BASE_URL=https://attacker.test",
                "https://example.test/v1",
            )

        self.assertFalse(path.exists())

    def test_secure_write_rejects_values_the_parser_would_reject(self):
        path = config.user_config_path(self.home)

        for api_key in ("sk-$(literal)", "sk-`literal`", "sk-${literal}"):
            with self.subTest(api_key=api_key):
                with self.assertRaisesRegex(config.ConfigError, "unsafe"):
                    config.write_user_config(path, api_key, "https://example.test/v1")

        self.assertFalse(path.exists())

    def test_secure_write_wraps_directory_creation_errors(self):
        blocker = self.root / "not-a-directory"
        blocker.write_text("block", encoding="utf-8")

        with self.assertRaisesRegex(config.ConfigError, "cannot write"):
            config.write_user_config(
                blocker / "env",
                "secret-key",
                "https://example.test/v1",
            )

    def test_secure_write_does_not_chmod_after_publishing(self):
        path = config.user_config_path(self.home)

        with mock.patch.object(config.os, "chmod") as chmod:
            config.write_user_config(path, "secret-key", "https://example.test/v1")

        chmod.assert_not_called()


if __name__ == "__main__":
    unittest.main()
