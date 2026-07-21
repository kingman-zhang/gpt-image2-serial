#!/usr/bin/env python3

import argparse
import base64
import binascii
import json
import os
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from config import ConfigError, resolve_config, user_config_path


def build_generation_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/images/generations"


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def request_json(url: str, api_key: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        raw = response.read()
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("The image API returned invalid JSON.") from exc


def download_image(url: str) -> bytes:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request) as response:
        return response.read()


def extract_image(response: dict[str, object]) -> bytes:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("The image API response did not include image data.")

    first = data[0]
    if not isinstance(first, dict):
        raise ValueError("The image API response did not include image data.")

    b64_json = first.get("b64_json")
    if isinstance(b64_json, str) and b64_json:
        try:
            return base64.b64decode(b64_json, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("The image API returned invalid Base64 image data.") from exc

    url = first.get("url")
    if isinstance(url, str) and url:
        return download_image(url)

    raise ValueError("The image API response did not include image data.")


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
        os.replace(temp_path, path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one image via an OpenAI-compatible API.")
    parser.add_argument("--out", required=True, help="Output file path.")
    parser.add_argument("--prompt", required=True, help="Image prompt.")
    parser.add_argument("--model", default="gpt-image-2", help="Image model.")
    parser.add_argument("--size", default="1536x864", help="Image size.")
    parser.add_argument("--quality", default="medium", help="Image quality.")
    parser.add_argument("--output-format", default="png", help="Image output format.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    destination = Path(args.out)
    if destination.exists():
        return fail(f"Refusing to overwrite existing output: {destination} already exists.")

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
            f"Run this setup wizard in an interactive terminal: python3 {configure_script}\n"
            "Do not paste your API key into chat."
        )

    api_key = image_config.api_key
    base_url = image_config.base_url
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
        "response_format": "b64_json",
    }

    try:
        response = request_json(build_generation_url(base_url), api_key, payload)
        image_bytes = extract_image(response)
        atomic_write(destination, image_bytes)
        print(destination)
        return 0
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return fail("Image generation failed: check your API credentials or endpoint access.")
        if exc.code == 429:
            return fail(
                "Image generation is rate or concurrency limited. Wait for the current job to finish, then retry serially."
            )
        return fail(f"Image generation failed with HTTP {exc.code}.")
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            return fail(
                "Image generation hit a TLS or proxy error. Confirm network/proxy settings before retrying."
            )
        return fail(f"Image generation failed due to a network error: {exc.reason}")
    except ssl.SSLError:
        return fail(
            "Image generation hit a TLS or proxy error. Confirm network/proxy settings before retrying."
        )
    except ValueError as exc:
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
