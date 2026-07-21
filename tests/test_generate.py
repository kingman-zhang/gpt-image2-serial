import base64
import http.server
import json
import os
import socket
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "gpt-image2-serial" / "scripts" / "generate.py"


class FixtureHandler(http.server.BaseHTTPRequestHandler):
    response_mode = "b64"
    image_bytes = b"image-bytes"
    records = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8")
        payload = json.loads(body)
        self.__class__.records.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "payload": payload,
            }
        )

        if self.__class__.response_mode == "b64":
            self._send_json(
                200,
                {
                    "data": [
                        {
                            "b64_json": base64.b64encode(self.__class__.image_bytes).decode(
                                "ascii"
                            )
                        }
                    ]
                },
            )
            return
        if self.__class__.response_mode == "url":
            self._send_json(
                200,
                {"data": [{"url": f"http://127.0.0.1:{self.server.server_port}/download"}]},
            )
            return
        if self.__class__.response_mode == "401":
            self._send_json(401, {"error": {"message": "bad key"}})
            return
        if self.__class__.response_mode == "429":
            self._send_json(429, {"error": {"message": "rate limited"}})
            return
        if self.__class__.response_mode == "malformed":
            self._send_json(200, {"data": [{}]})
            return
        raise AssertionError(f"Unexpected response mode: {self.__class__.response_mode}")

    def do_GET(self):
        if self.path != "/download":
            self.send_error(404)
            return
        self.__class__.records.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(self.__class__.image_bytes)))
        self.end_headers()
        self.wfile.write(self.__class__.image_bytes)

    def log_message(self, fmt, *args):
        return

    def _send_json(self, status, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class GenerateScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FixtureHandler.records = []
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.server = server
        cls.thread = threading.Thread(target=server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{server.server_port}/v1/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        FixtureHandler.records = []
        FixtureHandler.response_mode = "b64"
        FixtureHandler.image_bytes = b"expected-image"
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.output_path = Path(self.tempdir.name) / "out.png"

    def run_script(self, extra_args=None, env=None):
        args = [
            "python3",
            str(SCRIPT),
            "--out",
            str(self.output_path),
            "--prompt",
            "test prompt",
            "--model",
            "gpt-image-2",
            "--size",
            "1536x864",
            "--quality",
            "medium",
            "--output-format",
            "png",
        ]
        if extra_args:
            args.extend(extra_args)
        merged_env = os.environ.copy()
        merged_env.update(
            {
                "OPENAI_IMAGE_API_KEY": "test-secret",
                "OPENAI_IMAGE_BASE_URL": self.base_url,
                "NO_PROXY": "127.0.0.1,localhost",
                "no_proxy": "127.0.0.1,localhost",
                "HTTP_PROXY": "",
                "HTTPS_PROXY": "",
                "http_proxy": "",
                "https_proxy": "",
                }
        )
        if env:
            merged_env.update(env)
        return subprocess.run(args, capture_output=True, text=True, env=merged_env)

    def test_base64_response_writes_image_atomically(self):
        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output_path.read_bytes(), b"expected-image")
        self.assertEqual(len(FixtureHandler.records), 1)
        request = FixtureHandler.records[0]
        self.assertEqual(request["path"], "/v1/images/generations")
        self.assertEqual(request["authorization"], "Bearer test-secret")
        self.assertEqual(
            request["payload"],
            {
                "model": "gpt-image-2",
                "prompt": "test prompt",
                "size": "1536x864",
                "quality": "medium",
                "output_format": "png",
                "response_format": "b64_json",
            },
        )
        leftovers = list(self.output_path.parent.glob("*.tmp"))
        self.assertEqual(leftovers, [])

    def test_url_response_downloads_image(self):
        FixtureHandler.response_mode = "url"
        FixtureHandler.image_bytes = b"url-image"

        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output_path.read_bytes(), b"url-image")
        self.assertEqual(FixtureHandler.records[1]["path"], "/download")
        self.assertIsNone(FixtureHandler.records[1]["authorization"])

    def test_base_url_trailing_slash_is_normalized(self):
        result = self.run_script(env={"OPENAI_IMAGE_BASE_URL": self.base_url.rstrip("/")})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(FixtureHandler.records[0]["path"], "/v1/images/generations")

    def test_existing_output_is_rejected(self):
        self.output_path.write_bytes(b"existing")

        result = self.run_script()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(self.output_path.read_bytes(), b"existing")
        self.assertEqual(FixtureHandler.records, [])

    def test_401_hides_api_key(self):
        FixtureHandler.response_mode = "401"

        result = self.run_script()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("credentials", result.stderr.lower())
        self.assertNotIn("test-secret", result.stderr)
        self.assertFalse(self.output_path.exists())

    def test_429_recommends_serial_retry(self):
        FixtureHandler.response_mode = "429"

        result = self.run_script()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wait", result.stderr.lower())
        self.assertIn("serial", result.stderr.lower())
        self.assertFalse(self.output_path.exists())

    def test_malformed_response_leaves_no_output(self):
        FixtureHandler.response_mode = "malformed"

        result = self.run_script()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("image data", result.stderr.lower())
        self.assertFalse(self.output_path.exists())


if __name__ == "__main__":
    unittest.main()
