# gpt-image2-serial

[English](./README.en.md)

这是一个面向 Codex、Claude Code 以及其他支持 `SKILL.md` 约定的 Agent 的可移植技能包，用来通过 OpenAI-compatible images API 稳定地串行生成 GPT Image 2 图片。

## 它解决什么问题

- 严格一次只生成一张图，避免并发限制和多任务互相干扰
- 自带独立 Python 客户端，不依赖第三方库
- 通过环境变量或 `.env.image` 管理 API key 和 base URL
- 技能主体放在 `skills/gpt-image2-serial`，方便直接安装到常见 Agent 技能目录

## 快速安装

### 使用 skills installer

如果本机有 Node.js，可以直接运行：

```bash
npx skills add kingman-zhang/gpt-image2-serial
```

项目地址：[https://github.com/kingman-zhang/gpt-image2-serial](https://github.com/kingman-zhang/gpt-image2-serial)

### 让 Codex 自动安装

把下面的提示词直接发给 Codex：

```text
请帮我从这个 GitHub 仓库安装 skill：
https://github.com/kingman-zhang/gpt-image2-serial

要安装的 skill 位于仓库中的 skills/gpt-image2-serial。
请优先使用当前环境可用的 skills installer；如果没有 installer，
就将该目录安装到我的 Codex skills 目录。
安装完成后，请检查 SKILL.md 是否存在，并确认 Codex 能发现
gpt-image2-serial。若需要重启 Codex 才能加载，也请告诉我。
```

这里同时给出完整 GitHub 地址和仓库内的 skill 路径，Agent 不需要猜测项目来自哪个平台，也不会误把整个仓库当作一个 skill。

### 让 Claude Code 或其他 Agent 自动安装

```text
请帮我从这个 GitHub 仓库安装 skill：
https://github.com/kingman-zhang/gpt-image2-serial

要安装的 skill 位于仓库中的 skills/gpt-image2-serial。
请优先使用当前环境可用的 skills installer；如果没有 installer，
就将该目录安装到当前 Agent 的 skills 目录。
安装完成后，请检查 SKILL.md 是否存在，并确认当前 Agent 能发现
gpt-image2-serial。若需要重启 Agent 才能加载，也请告诉我。
```

### 手动安装

先克隆仓库：

```bash
git clone https://github.com/kingman-zhang/gpt-image2-serial.git
cd gpt-image2-serial
```

安装到 Codex：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/gpt-image2-serial "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装到 Claude Code：

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/gpt-image2-serial "$HOME/.claude/skills/"
```

## 运行要求

- Python 3
- 能访问 OpenAI-compatible images endpoint 的网络环境
- 一个具备图片生成权限的 API key

## 配置 API Key 和 URL

推荐环境变量：

```bash
export OPENAI_IMAGE_API_KEY="your-key"
export OPENAI_IMAGE_BASE_URL="https://api.openai.com/v1"   # 可选
```

兼容回退变量：

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"   # 可选
```

如果你希望按项目单独配置，也可以使用：

```bash
cp .env.image.example .env.image
```

然后在 `.env.image` 里填入你自己的值。

不要提交 `.env.image`，不要把真实 key 粘贴进 prompt，也不要把密钥硬编码进 skill 或脚本。

## 使用示例

```bash
./skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh \
  --out assets/example.png \
  --size 1536x864 \
  --quality medium \
  --prompt "一张柔和自然光的编辑风封面图"
```

也可以让 Agent 显式调用这个技能，例如在提示词里写 `$gpt-image2-serial`。

## 仓库结构

```text
skills/gpt-image2-serial/
├── SKILL.md
├── agents/openai.yaml
└── scripts/
    ├── generate.py
    └── gpt-image2-serial-generate.sh
```
