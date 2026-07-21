# gpt-image2-serial

[中文](./README.md)

A portable skill package for Codex, Claude Code, and other agents that support the `SKILL.md` convention. It provides reliable, one-at-a-time GPT Image 2 generation through an OpenAI-compatible images API.

## What It Solves

- Strict single-image generation to avoid concurrency issues
- A standalone Python client with no third-party dependencies
- A secure wizard for user-level API configuration, plus environment and project overrides
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
Codex must be restarted to load it. Then check whether the image API is
configured. If it is not, start the skill's secure setup wizard and let me
enter the key privately in the terminal. Do not ask me to paste it into chat.
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
gpt-image2-serial. Tell me if the agent must be restarted to load it. Then
check whether the image API is configured. If it is not, start the skill's
secure setup wizard and let me enter the key privately in the terminal. Do
not ask me to paste it into chat.
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

- Python 3.10 or later
- Network access to an OpenAI-compatible images endpoint
- An API key with image generation permission

## Configure the Image API

The recommended method is the skill's secure setup wizard. It saves configuration to:

```text
~/.config/gpt-image2-serial/env
```

`~` is your user home directory. Configure it once and use the skill from any project. The file is created with mode `0600`, so only your user can read or write it.

### Ask an agent to configure it

Send this prompt to Codex, Claude Code, or another agent:

```text
Please start the secure setup wizard for gpt-image2-serial.
Show me the full configuration path and let me enter the API key privately
in the terminal. Do not ask me to paste the API key into chat.
After configuration succeeds, continue my original image generation task.
```

If the agent provides a terminal you can operate directly, it starts the wizard. Otherwise, it gives you a complete command to run in your own terminal. The key is hidden while you type it. Press Enter at the Base URL prompt to use `https://api.openai.com/v1`.

### Configure it manually in a terminal

Codex:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2-serial/scripts/configure.py"
```

Claude Code:

```bash
python3 "$HOME/.claude/skills/gpt-image2-serial/scripts/configure.py"
```

The wizard displays the full destination path before asking for input. Run the same command again to update the configuration; it asks before replacing an existing file.

To remove the configuration:

```bash
rm "$HOME/.config/gpt-image2-serial/env"
```

Never paste a real API key into prompts, command arguments, screenshots, or logs.

### Advanced configuration

Environment variables remain supported and have the highest priority:

Preferred variables:

```bash
export OPENAI_IMAGE_API_KEY="your-key"
export OPENAI_IMAGE_BASE_URL="https://api.openai.com/v1"   # optional
```

Compatibility variables:

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"   # optional
```

If you cloned this repository and need a per-project override, run this from the repository root:

```bash
cp .env.image.example .env.image
```

The project-level `.env.image` overrides user-level configuration but not environment variables. Never commit `.env.image`.

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
    ├── config.py
    ├── configure.py
    ├── generate.py
    └── gpt-image2-serial-generate.sh
```
