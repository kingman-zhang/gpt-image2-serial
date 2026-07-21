---
name: gpt-image2-serial
description: Use this when generating GPT Image 2 or other OpenAI-compatible images reliably through a portable local skill, especially when concurrency limits or fragile environments require strict one-at-a-time execution.
---

# gpt-image2-serial

Use this skill when an agent needs reliable, serial image generation through an OpenAI-compatible images API.

## Rules

- Generate exactly one image at a time. Wait until the command exits before starting another.
- Use the bundled wrapper `scripts/gpt-image2-serial-generate.sh`.
- Keep outputs inside the active workspace unless the user explicitly chooses another path.
- Never overwrite an existing output file unless the user clearly asked for replacement.
- Do not display API key values in messages, logs, or screenshots.

## Quick Workflow

1. Check whether `OPENAI_IMAGE_API_KEY` or `OPENAI_API_KEY` is configured, without echoing the value.
2. If neither key exists, ask the user to export a key or create a project-local `.env.image`.
3. Run exactly one command with the bundled wrapper:

```bash
./skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh \
  --out assets/example.png \
  --size 1536x864 \
  --quality medium \
  --prompt "..."
```

4. Wait for completion before issuing another generation.
5. Verify the output file exists and is the expected image.

## Configuration

- Preferred API key variable: `OPENAI_IMAGE_API_KEY`
- Fallback API key variable: `OPENAI_API_KEY`
- Preferred base URL variable: `OPENAI_IMAGE_BASE_URL`
- Fallback base URL variable: `OPENAI_BASE_URL`
- Default base URL: `https://api.openai.com/v1`
- Optional project-local config file: `.env.image`

## Failure Handling

- `429` rate or concurrency limiting: wait for the prior request to finish, then retry the same single image serially.
- TLS or proxy record-layer failures: report a likely network or proxy problem and ask before changing proxy behavior.
- Missing key: tell the user to set `OPENAI_IMAGE_API_KEY` or create `.env.image`.
- Existing output path: keep the existing file and choose a versioned filename instead of overwriting implicitly.

## Prompt Guidance

- Prefer one command per output image.
- Use `1536x864` for wide covers and `1536x1152` for 4:3 layouts.
- Use `medium` quality by default for a balance of speed and reliability.
- If the final asset needs title text, prefer adding it later in layout tools instead of baking text into the generated image.
