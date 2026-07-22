# Windows 可见安全配置向导设计

## 背景

在 Windows Codex 中，Agent 可能在自己的后台终端启动配置向导，然后告诉用户“向导已在终端等待”。用户实际看不到这个后台终端，也无法输入 API key，只能再次要求 Agent 打开一个可见窗口。

问题不在 Python 配置向导本身，而在 Agent 对终端可见性的判断和说明。后台 PTY 与用户能够直接操作的 PowerShell 窗口不是同一种交互界面。

## 目标

- Windows 用户缺少 API 配置时，优先获得独立、可见、可操作的 PowerShell 窗口。
- Agent 只有在确认窗口成功启动后，才能声称向导已经打开。
- 无法打开或确认窗口时，不留下等待输入的后台向导。
- 用户始终能获得一条可复制的完整 PowerShell 命令。
- API key 继续使用隐藏输入，不进入聊天记录、命令参数或 Agent 日志。

## 非目标

- 不修改用户级配置文件格式或保存路径。
- 不修改 `configure.py` 的输入和写入逻辑。
- 不为 Windows 增加图形化配置程序。
- 不保证所有 Agent 都有权限启动桌面窗口。

## Windows 默认流程

当 Windows 上缺少 API 配置时，Agent 按以下顺序处理：

1. 判断当前终端是否由用户直接可见、可操作。
2. 如果只是 Agent 后台 PTY，不在其中启动需要用户输入的向导。
3. 尝试启动独立 PowerShell 窗口，并在其中运行已安装 skill 的 `configure.py`。
4. 确认窗口启动命令成功后，告诉用户查看任务栏中新出现的 Windows PowerShell 或 PowerShell 窗口。
5. 等待用户明确表示配置完成，不自行假定输入已经结束。
6. 检查 `%USERPROFILE%\.config\gpt-image2-serial\env` 是否存在且非空，不读取或回显 key。
7. 配置有效后继续用户原来的图片生成请求。

## PowerShell 命令

用户在自己的 PowerShell 中运行的首选命令：

```powershell
py "$env:USERPROFILE\.codex\skills\gpt-image2-serial\scripts\configure.py"
```

如果系统没有 Python Launcher，则使用：

```powershell
python "$env:USERPROFILE\.codex\skills\gpt-image2-serial\scripts\configure.py"
```

Agent 自动打开独立窗口时，使用 PowerShell 的 `Start-Process`，保留窗口以便用户看到成功或错误信息。文档只描述目标行为，不绑定某个 Agent 的内部 UI 工具；Agent 应使用当前环境允许的桌面启动能力。

## 确认与回退

“启动命令已提交”不等于“用户看到了窗口”。Agent 只有获得窗口启动成功的直接结果时，才能说“已打开独立 PowerShell 窗口”。

如果不能确认窗口可见，Agent 必须：

1. 停止或清理自己启动的后台向导进程。
2. 明确说明当前 Agent 无法提供用户可操作的终端。
3. 显示首选 `py` 命令和 `python` 回退命令。
4. 请用户在自己的 PowerShell 中运行，并在完成后回复“配置完成”。

Agent 不得使用“向导正在终端等待”“请切换到终端”等模糊说法，除非同时说明具体窗口名称和用户能在哪里找到它。

## macOS 与 Linux

现有安全原则保持不变：只有用户能直接操作的终端才适合运行向导。Agent 后台 PTY 同样不能被描述为用户可见终端。

如果无法提供可操作终端，显示对应平台的完整命令，让用户在自己的终端运行。

## 文档调整

中文 README 增加独立的 Windows 配置说明，包含：

- 为什么可能看不到后台向导
- 正常情况下应出现独立 PowerShell 窗口
- 在任务栏中查找 Windows PowerShell 或 PowerShell
- `py` 首选命令和 `python` 回退命令
- 没有出现窗口时的处理步骤
- 配置文件的 Windows 完整位置表达

英文 README 同步相同内容。

`SKILL.md` 增加跨平台硬性规则：不要把 Agent 后台 PTY 称为用户可见终端。Windows 上优先打开独立 PowerShell；无法确认时立即回退为完整命令。

Agent 安装提示词增加 Windows 可见窗口要求，避免安装后首次配置再次进入不可见后台等待状态。

## 错误处理

- `py` 不存在：提示改用 `python`。
- `python` 也不存在：说明需要先安装 Python 3.10 或更高版本，并停止配置流程。
- 独立窗口启动失败：不声称向导已打开，直接显示手动命令。
- 窗口已打开但用户找不到：提示查看任务栏，并允许改用手动命令。
- 用户取消向导：不继续图片生成，保留原始请求上下文。
- 后台向导误启动：终止该后台进程后再回退，避免遗留等待输入的任务。

## 验证

文档与 skill 验证包括：

- README 中同时存在 `py` 和 `python` 两种 Windows 命令。
- `SKILL.md` 明确禁止把后台 PTY 描述为用户可见终端。
- Windows 流程要求确认独立窗口成功后才能通知用户。
- 失败回退包含可复制的完整命令。
- 配置完成验证只检查文件存在和非空，不输出敏感值。
- 中英文 README 内容保持一致。

## 验收标准

- Windows 用户第一次配置时，不再收到无法定位的“向导正在终端等待”提示。
- 自动打开成功时，用户能在任务栏找到独立 PowerShell 窗口。
- 自动打开失败时，用户立即获得可执行命令，而不是等待隐藏进程。
- 用户无需把 API key 发到聊天中。
- 配置完成后，Agent 可以继续原来的图片生成任务。
