#!/usr/bin/env python3

import getpass
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from config import (
    DEFAULT_BASE_URL,
    ConfigError,
    user_config_path,
    validate_base_url,
    write_user_config,
)


def run(
    *,
    home: Path | None = None,
    input_fn: Callable[[str], str] = input,
    secret_fn: Callable[[str], str] = getpass.getpass,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    path = user_config_path(home).expanduser()
    print(f"Image API configuration will be saved to: {path}", file=stdout)

    if path.exists():
        answer = input_fn("Configuration already exists. Replace it? [y/N]: ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Configuration was not changed.", file=stdout)
            return 0

    api_key = ""
    while not api_key:
        api_key = secret_fn("OpenAI-compatible image API key (input hidden): ")
        if not api_key:
            print("API key cannot be empty. Please try again.", file=stderr)

    base_url_input = input_fn(f"Base URL [{DEFAULT_BASE_URL}]: ").strip()
    try:
        base_url = validate_base_url(base_url_input or DEFAULT_BASE_URL)
        write_user_config(path, api_key, base_url)
    except ConfigError as exc:
        print(f"Configuration failed: {exc}", file=stderr)
        return 1

    print(f"Configuration saved securely to: {path}", file=stdout)
    print("You can now retry the original image generation request.", file=stdout)
    return 0


def main() -> int:
    if not sys.stdin.isatty():
        command = f"python3 {Path(__file__).resolve()}"
        print(
            "An interactive terminal is required so the API key can be entered securely.\n"
            f"Run this command in your terminal: {command}",
            file=sys.stderr,
        )
        return 1
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
