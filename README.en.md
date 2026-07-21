# gpt-image2-serial

[中文](./README.md)

A portable skill package for Codex, Claude Code, and other agents that support the `SKILL.md` convention. It provides reliable, one-at-a-time GPT Image 2 generation through an OpenAI-compatible images API.

## What It Solves

- Strict single-image generation to avoid concurrency issues
- A standalone Python client with no third-party dependencies
- Safe API key and base URL handling through environment variables or `.env.image`
- A portable skill package under `skills/gpt-image2-serial` for common agent skill directories

## Quick Install

### Use a skills installer

If Node.js is available, run:

```bash
npx skills add kingman-zhang/gpt-image2-serial
```

Project: [https://github.com/kingman-zhang/gpt-image2-serial](https://github.com/kingman-zhang/gpt-image2-serial)

### Ask Codex to install it

Send this prompt to Codex:

```text
Please install the skill from this GitHub repository:
https://github.com/kingman-zhang/gpt-image2-serial

The skill is located at skills/gpt-image2-serial within the repository.
Use an available skills installer if possible. Otherwise, install that
directory into my Codex skills directory. After installation, check that
SKILL.md exists and that Codex can discover gpt-image2-serial. Tell me if
Codex must be restarted to load it.
```

The full URL identifies GitHub as the source, while the explicit subdirectory prevents the agent from treating the whole repository as one skill.

### Ask Claude Code or another agent to install it

```text
Please install the skill from this GitHub repository:
https://github.com/kingman-zhang/gpt-image2-serial

The skill is located at skills/gpt-image2-serial within the repository.
Use an available skills installer if possible. Otherwise, install that
directory into the current agent's skills directory. After installation,
check that SKILL.md exists and that the agent can discover
gpt-image2-serial. Tell me if the agent must be restarted to load it.
```

### Manual installation

Clone the repository first:

```bash
git clone https://github.com/kingman-zhang/gpt-image2-serial.git
cd gpt-image2-serial
```

Install for Codex:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/gpt-image2-serial "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Install for Claude Code:

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
