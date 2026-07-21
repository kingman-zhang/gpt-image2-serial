# gpt-image2-serial

[中文](./README.md)

A portable skill package for Codex, Claude Code, and other agents that support the `SKILL.md` convention. It provides reliable, one-at-a-time GPT Image 2 generation through an OpenAI-compatible images API.

## What It Solves

- Strict single-image generation to avoid concurrency issues
- A standalone Python client with no third-party dependencies
- Safe API key and base URL handling through environment variables or `.env.image`
- A portable skill package under `skills/gpt-image2-serial` for common agent skill directories

## Install

Install with a common skills installer:

```bash
npx skills add kingman-zhang/gpt-image2-serial
```

GitHub repository: `kingman-zhang/gpt-image2-serial`

Manual install for Codex:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/gpt-image2-serial "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Manual install for Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/gpt-image2-serial "$HOME/.claude/skills/"
```

## Requirements

- Python 3
- Network access to an OpenAI-compatible images endpoint
- An API key with image generation permission

## Configure API Key and URL

Preferred environment variables:

```bash
export OPENAI_IMAGE_API_KEY="your-key"
export OPENAI_IMAGE_BASE_URL="https://api.openai.com/v1"   # optional
```

Compatibility fallback variables:

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional
```

If you prefer project-local configuration:

```bash
cp .env.image.example .env.image
```

Then fill in `.env.image` with your own values.

Never commit `.env.image`, never paste real secrets into prompts, and never hard-code credentials into the skill.

## Usage

```bash
./skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh \
  --out assets/example.png \
  --size 1536x864 \
  --quality medium \
  --prompt "A calm editorial cover image with soft natural light"
```

Agents can also invoke the skill explicitly with `$gpt-image2-serial`.

## Repository Layout

```text
skills/gpt-image2-serial/
├── SKILL.md
├── agents/openai.yaml
└── scripts/
    ├── generate.py
    └── gpt-image2-serial-generate.sh
```
