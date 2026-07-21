#!/usr/bin/env python3

import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_BASE_URL = "https://api.openai.com/v1"
USER_CONFIG_RELATIVE_PATH = Path(".config") / "gpt-image2-serial" / "env"
PROJECT_CONFIG_NAME = ".env.image"
ALLOWED_KEYS = {"OPENAI_IMAGE_API_KEY", "OPENAI_IMAGE_BASE_URL"}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ImageConfig:
    api_key: str | None
    base_url: str


def user_config_path(home: Path | None = None) -> Path:
    return (home or Path.home()) / USER_CONFIG_RELATIVE_PATH


def _parse_value(value: str, path: Path, line_number: int) -> str:
    value = value.strip()
    if value.startswith(("'", '"')):
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise ConfigError(f"{path}:{line_number}: unmatched quote")
        value = value[1:-1]

    if any(marker in value for marker in ("$(", "${", "`", "\x00", "\r", "\n")):
        raise ConfigError(f"{path}:{line_number}: unsafe value syntax")
    return value


def read_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export ") or "=" not in line:
            raise ConfigError(f"{path}:{line_number}: expected KEY=VALUE")

        key, raw_value = line.split("=", 1)
        key = key.strip()
        if key not in ALLOWED_KEYS:
            raise ConfigError(f"{path}:{line_number}: unknown configuration key {key!r}")
        values[key] = _parse_value(raw_value, path, line_number)

    return values


def validate_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ConfigError("base URL must be an absolute http:// or https:// URL")
    return value


def resolve_config(
    environ: Mapping[str, str] | None = None,
    project_dir: Path | None = None,
    home: Path | None = None,
) -> ImageConfig:
    environment = os.environ if environ is None else environ
    project = project_dir or Path.cwd()
    user_values = read_dotenv(user_config_path(home))
    project_values = read_dotenv(project / PROJECT_CONFIG_NAME)

    api_key = (
        environment.get("OPENAI_IMAGE_API_KEY")
        or environment.get("OPENAI_API_KEY")
        or project_values.get("OPENAI_IMAGE_API_KEY")
        or user_values.get("OPENAI_IMAGE_API_KEY")
        or None
    )
    base_url = (
        environment.get("OPENAI_IMAGE_BASE_URL")
        or environment.get("OPENAI_BASE_URL")
        or project_values.get("OPENAI_IMAGE_BASE_URL")
        or user_values.get("OPENAI_IMAGE_BASE_URL")
        or DEFAULT_BASE_URL
    )
    return ImageConfig(api_key=api_key, base_url=validate_base_url(base_url))


def write_user_config(path: Path, api_key: str, base_url: str) -> None:
    if not api_key:
        raise ConfigError("API key cannot be empty")
    if any(character in api_key for character in ("\n", "\r", "\x00")):
        raise ConfigError("API key contains invalid line-breaking characters")

    normalized_base_url = validate_base_url(base_url)
    content = (
        f"OPENAI_IMAGE_API_KEY={api_key}\n"
        f"OPENAI_IMAGE_BASE_URL={normalized_base_url}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        raise ConfigError(f"cannot write {path}: {exc}") from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
