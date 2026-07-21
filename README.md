# gpt-image2-serial

Portable `SKILL.md` package for reliable GPT Image 2 generation through an OpenAI-compatible images API. It is designed for Codex, Claude Code, and similar agents that can install skills from a repository.

## What This Gives You

- One-image-at-a-time generation to avoid concurrency surprises
- A standalone Python client with no third-party dependencies
- Safe handling of API keys through environment variables or `.env.image`
- A portable skill package under `skills/gpt-image2-serial`

## Install

One-command install with a common skills installer:

```bash
npx skills add <github-owner>/gpt-image2-serial
```

Replace `<github-owner>` after this repository is published.

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

## Configure Credentials

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

Project-local alternative:

```bash
cp .env.image.example .env.image
```

Then fill in `.env.image` with your own values.

Never commit `.env.image`, never paste real keys into prompts, and never hard-code secrets into the skill.

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
