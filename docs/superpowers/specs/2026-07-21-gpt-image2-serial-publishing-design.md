# GPT Image 2 Serial Publishing Design

## Goal

Publish the existing `gpt-image2-serial` skill as a GitHub repository that can be installed by Codex, Claude Code, and other agents that support the common `SKILL.md` convention. Remove the runtime dependency on Codex's bundled image generation implementation and keep credentials out of version control.

## Repository Layout

Keep repository-facing documentation separate from the installable skill package:

```text
repository/
|-- README.md
|-- LICENSE
|-- .gitignore
|-- .env.image.example
|-- docs/
|   `-- superpowers/specs/
`-- skills/
    `-- gpt-image2-serial/
        |-- SKILL.md
        |-- agents/openai.yaml
        `-- scripts/
            |-- generate.py
            `-- gpt-image2-serial-generate.sh
```

The repository root explains installation and configuration. The installable package remains concise and contains only agent instructions, metadata, and runtime scripts.

## Runtime Architecture

The shell wrapper is the stable command-line entry point. It locates the bundled Python client, optionally loads `.env.image` from the caller's current working directory, validates arguments, and then invokes the client once.

The Python client uses only the Python standard library. It sends an OpenAI-compatible request to `POST /images/generations`, accepts either `b64_json` image data or a returned image URL, and writes the result to the requested project-local path.

The wrapper must never start concurrent jobs. Each invocation blocks until its single request completes.

## Configuration Contract

Use these variables in priority order:

| Purpose | Preferred | Compatibility fallback | Default |
| --- | --- | --- | --- |
| API key | `OPENAI_IMAGE_API_KEY` | `OPENAI_API_KEY` | none |
| API base URL | `OPENAI_IMAGE_BASE_URL` | `OPENAI_BASE_URL` | `https://api.openai.com/v1` |

Normalize the base URL so both `https://host/v1` and `https://host/v1/` produce `https://host/v1/images/generations`.

Support a project-local `.env.image` for per-project configuration. Do not commit that file. Commit `.env.image.example` with empty placeholders and explanatory comments. Never print secret values in normal output or errors.

When the API key is absent, stop before making a network request and print exact instructions for either exporting `OPENAI_IMAGE_API_KEY` or creating `.env.image`.

## Command Interface

Preserve the existing public flags:

- Required: `--out`, `--prompt`
- Optional: `--model`, `--size`, `--quality`, `--output-format`
- Defaults: `gpt-image-2`, `1536x864`, `medium`, `png`

Reject unknown arguments, missing values, and an existing output file. Create the output parent directory only after configuration and arguments are valid.

## API and Error Handling

Send the model, prompt, size, quality, and output format in the generation request. Request Base64 output when accepted by the endpoint, while also supporting URL responses.

Handle failures with concise actionable messages:

- `401` or `403`: report invalid credentials or endpoint authorization without exposing the key.
- `429`: identify rate or concurrency limiting and instruct the agent to wait before retrying serially.
- TLS or proxy record-layer errors: identify the likely network/proxy failure and require user approval before changing proxy behavior.
- Invalid JSON, missing image data, or download failure: stop without leaving a successful-looking output.
- Existing output: refuse to overwrite it.

Write image bytes to a temporary file in the destination directory and atomically rename it only after a complete successful response.

## Agent Guidance

Update `SKILL.md` to:

- Trigger for reliable GPT Image 2 generation and OpenAI-compatible image endpoints.
- Require exactly one generation at a time.
- Prefer the bundled wrapper instead of any platform-specific internal script.
- Prompt for required environment configuration when absent.
- Keep output inside the active workspace unless the user explicitly chooses another location.
- Preserve the existing retry, proxy, aspect-ratio, and prompt guidance where it remains platform independent.

Add `agents/openai.yaml` with display metadata and a default prompt that explicitly invokes `$gpt-image2-serial`.

## Installation Documentation

The root README documents:

- One-command installation through a common skills installer using the GitHub repository URL.
- Manual installation into Codex and Claude Code skill directories.
- Required Python and network prerequisites.
- Environment-variable and `.env.image` setup.
- A minimal generation example.
- A warning never to commit `.env.image` or expose API keys in prompts.

Installation documentation uses placeholders for the GitHub owner and repository until the remote is configured.

## Verification

Validate the skill metadata with the standard skill validator. Test locally without making a paid image request:

1. Shell and Python syntax checks.
2. Help output and argument validation.
3. Missing-key guidance.
4. Existing-output protection.
5. Mock HTTP server tests for Base64 output, URL output, authentication failure, rate limiting, malformed responses, base URL normalization, and atomic writes.
6. Repository scan for likely API keys, hard-coded private URLs, proxy addresses, and local absolute paths.

Live generation is optional because it incurs network access and API cost; run it only with explicit user approval.
