# gpt-image2-serial

[English](./README.en.md)

这是一个面向 Codex、Claude Code 以及其他支持 `SKILL.md` 约定的 Agent 的可移植技能包，用来通过 OpenAI-compatible images API 稳定地串行生成 GPT Image 2 图片。

## 它解决什么问题

- 严格一次只生成一张图，避免并发限制和多任务互相干扰
- 自带独立 Python 客户端，不依赖第三方库
- 通过安全向导管理用户级 API 配置，也支持环境变量和项目级覆盖
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
再检查图片 API 是否已经配置；如果没有，请启动 skill 自带的
安全配置向导，让我在终端中隐藏输入。不要让我把 API key 发到聊天里。
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
再检查图片 API 是否已经配置；如果没有，请启动 skill 自带的
安全配置向导，让我在终端中隐藏输入。不要让我把 API key 发到聊天里。
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

- Python 3.10 或更高版本
- 能访问 OpenAI-compatible images endpoint 的网络环境
- 一个具备图片生成权限的 API key

## 配置图片 API

推荐使用 skill 自带的安全配置向导。它会把配置保存到：

```text
~/.config/gpt-image2-serial/env
```

`~` 代表你的用户主目录。配置一次后，所有项目都可以使用，不需要寻找“项目根目录”。配置文件只允许当前用户读写，权限为 `0600`。

### 让 Agent 帮你配置

把下面这段提示词发给 Codex、Claude Code 或其他 Agent：

```text
请为 gpt-image2-serial 启动安全配置向导。
请告诉我配置文件的完整保存路径，并让我在终端中隐藏输入 API key。
不要让我把 API key 发到聊天里。
配置成功后，请继续我原来的图片生成任务。
```

如果当前 Agent 提供你可以直接操作的交互终端，它会启动向导；否则会给出一条完整命令，请在你自己的终端中运行。输入 API key 时屏幕不会显示内容；Base URL 直接回车会使用 `https://api.openai.com/v1`。

### 在终端手动配置

Codex：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2-serial/scripts/configure.py"
```

Claude Code：

```bash
python3 "$HOME/.claude/skills/gpt-image2-serial/scripts/configure.py"
```

向导会先显示配置文件的完整路径。再次运行同一命令即可更新配置；向导在覆盖前会询问确认。

如需删除配置：

```bash
rm "$HOME/.config/gpt-image2-serial/env"
```

不要把真实 API key 粘贴进 prompt、命令参数、截图或日志。

### 高级配置

环境变量仍然受支持，并且优先级最高：

```bash
export OPENAI_IMAGE_API_KEY="your-key"
export OPENAI_IMAGE_BASE_URL="https://api.openai.com/v1"   # 可选
```

兼容变量：

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"   # 可选
```

如果已经克隆本仓库，并希望只覆盖当前项目，可以在仓库根目录运行：

```bash
cp .env.image.example .env.image
```

项目级 `.env.image` 会覆盖用户级配置，但不会覆盖环境变量。不要提交 `.env.image`。

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
    ├── config.py
    ├── configure.py
    ├── generate.py
    └── gpt-image2-serial-generate.sh
```
