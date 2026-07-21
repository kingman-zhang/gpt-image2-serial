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

1. 先检查 `OPENAI_IMAGE_API_KEY` 或 `OPENAI_API_KEY` 是否已配置，但不要回显具体值。
2. 如果两个 key 都不存在，提示用户导出环境变量，或者创建项目级 `.env.image`。
3. 使用自带脚本执行单次生成：

```bash
./skills/gpt-image2-serial/scripts/gpt-image2-serial-generate.sh \
  --out assets/example.png \
  --size 1536x864 \
  --quality medium \
  --prompt "..."
```

4. 等待命令执行完成，再开始下一次生成。
5. 检查输出文件是否存在，并确认它就是预期图片。

## 配置约定

- 首选 API key 变量：`OPENAI_IMAGE_API_KEY`
- 兼容回退 API key 变量：`OPENAI_API_KEY`
- 首选 base URL 变量：`OPENAI_IMAGE_BASE_URL`
- 兼容回退 base URL 变量：`OPENAI_BASE_URL`
- 默认 base URL：`https://api.openai.com/v1`
- 可选项目级配置文件：`.env.image`

## 失败处理

- 遇到 `429` rate limit 或 concurrency limit：等待前一个请求完全结束，然后以串行方式重试同一张图。
- 遇到 TLS 或 proxy record-layer 错误：告诉用户这大概率是网络或代理问题，在修改代理行为前先征求确认。
- 缺少 key：提示用户设置 `OPENAI_IMAGE_API_KEY`，或者创建 `.env.image`。
- 输出路径已存在：保留现有文件，改用版本化文件名，不要直接覆盖。

## Prompt 建议

- 一张输出图对应一条命令。
- 横版封面优先使用 `1536x864`，4:3 布局优先使用 `1536x1152`。
- 默认优先使用 `medium` 质量，兼顾速度和稳定性。
- 如果最终图片还要加标题或排版文字，优先在后续设计工具里补，而不是直接把大量文字烘焙进生成图里。
