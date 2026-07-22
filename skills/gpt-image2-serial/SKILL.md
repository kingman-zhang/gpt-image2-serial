---
name: gpt-image2-serial
description: 用于稳定串行生成 GPT Image 2 或 OpenAI-compatible images；当需要 one-at-a-time execution、避免 concurrency limits、通过本地 portable skill 可靠出图时使用。
---

# gpt-image2-serial

当 Agent 需要通过 OpenAI-compatible images API 稳定、串行地生成图片时，使用这个 skill。

## 规则

- 一次只生成一张图，当前命令没有结束前，不要启动下一张。
- 使用 skill 自带的包装脚本 `scripts/gpt-image2-serial-generate.sh`。
- 输出文件默认放在当前工作区内，除非用户明确指定别的位置。
- 不要隐式覆盖已经存在的输出文件，除非用户明确要求替换。
- 不要在消息、日志或截图里暴露 API key 的实际值。

## 快速工作流

1. 检查环境变量、当前目录的 `.env.image` 和用户级 `~/.config/gpt-image2-serial/env` 是否可用，但不要读取或回显 key。
2. 如果缺少 key，告诉用户配置文件的完整路径，并在可交互终端中运行 `scripts/configure.py`。让用户在终端隐藏输入，不要要求用户把 key 发到聊天中。
3. 配置成功后继续原来的出图请求，不要求用户重新描述任务。
4. 使用自带脚本执行单次生成：

```bash
./skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh \
  --out assets/example.png \
  --size 1536x864 \
  --quality medium \
  --prompt "..."
```

5. 等待命令执行完成，再开始下一次生成。
6. 检查输出文件是否存在，并确认它就是预期图片。

## 安全配置

默认用户级配置文件为 `~/.config/gpt-image2-serial/env`，配置一次即可供所有项目使用。缺少配置时，在当前 skill 目录运行：

```bash
python3 scripts/configure.py
```

向导会显示实际保存路径并使用隐藏输入读取 key。在 macOS 和 Linux 上将文件权限设为 `0600`；Windows 上继承当前用户配置目录的访问控制权限。如果 Agent 无法提供可交互终端，给用户一条包含 `configure.py` 完整路径的命令，让用户在自己的终端运行。

配置优先级从高到低：

1. `OPENAI_IMAGE_API_KEY`、`OPENAI_IMAGE_BASE_URL`
2. `OPENAI_API_KEY`、`OPENAI_BASE_URL`
3. 当前工作目录的 `.env.image`
4. `~/.config/gpt-image2-serial/env`
5. 默认 base URL `https://api.openai.com/v1`

## 失败处理

- 遇到 `429` rate limit 或 concurrency limit：等待前一个请求完全结束，然后以串行方式重试同一张图。
- 遇到 TLS 或 proxy record-layer 错误：告诉用户这大概率是网络或代理问题，在修改代理行为前先征求确认。
- 缺少 key：启动 `scripts/configure.py`；不要让用户把 key 粘贴到聊天、命令参数或日志中。
- 输出路径已存在：保留现有文件，改用版本化文件名，不要直接覆盖。

## Prompt 建议

- 一张输出图对应一条命令。
- 横版封面优先使用 `1536x864`，4:3 布局优先使用 `1536x1152`。
- 默认优先使用 `medium` 质量，兼顾速度和稳定性。
- 如果最终图片还要加标题或排版文字，优先在后续设计工具里补，而不是直接把大量文字烘焙进生成图里。
