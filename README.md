# gpt-image2-serial

[English](./README.en.md)

这是一个面向 Codex、Claude Code 以及其他支持 `SKILL.md` 约定的 Agent 的可移植技能包，用来通过 OpenAI-compatible images API 稳定地串行生成 GPT Image 2 图片。

## 它解决什么问题

- 严格一次只生成一张图，避免并发限制和多任务互相干扰
- 自带独立 Python 客户端，不依赖第三方库
- 通过环境变量或 `.env.image` 管理 API key 和 base URL
- 技能主体放在 `skills/gpt-image2-serial`，方便直接安装到常见 Agent 技能目录

## 安装方式

使用通用 skills installer 一键安装：

```bash
npx skills add kingman-zhang/gpt-image2-serial
```

GitHub 仓库地址：`kingman-zhang/gpt-image2-serial`

让 Codex 帮你安装：

把下面这段 prompt 直接发给 Codex：

```text
请帮我安装这个 skill：kingman-zhang/gpt-image2-serial。
如果当前环境支持通用 skills installer，就直接安装；
否则请把仓库中的 skills/gpt-image2-serial 复制到我的 Codex skills 目录。
安装完成后，再检查它是否已经可用。
```

让 Claude Code 或其他 Agent 帮你安装：

```text
请帮我从 GitHub 仓库 kingman-zhang/gpt-image2-serial 安装这个 skill。
如果当前环境支持通用 skills installer，就直接安装；
否则请把仓库中的 skills/gpt-image2-serial 复制到当前 Agent 的 skills 目录。
安装完成后，请再验证这个 skill 是否已经可用。
```

手动安装到 Codex：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/gpt-image2-serial "${CODEX_HOME:-$HOME/.codex}/skills/"
```

手动安装到 Claude Code：

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
