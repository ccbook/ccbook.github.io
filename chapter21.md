# 第21章：Hook 系统——可编程的钩子

## 什么是 Hook？

"Hook"（钩子）这个词在编程中很常见。想象你在河边钓鱼——你在河流的某个点放下一个钩子，当鱼经过时钩子就会触发。

在 Claude Code 中，Hook 的概念类似：你在程序流程的某个"点"上放置一段代码，当程序执行到那个点时，你的代码就会被触发。

## 为什么需要 Hook？

假设你有以下需求：

- 每次 AI 要执行 `git push` 之前，先运行测试
- 每次会话结束后，把对话摘要保存到笔记本
- 每次 AI 修改文件后，自动运行代码格式化工具
- 每次提交消息前，检查有没有包含敏感信息

这些需求有一个共同点：**在某个事件发生时，自动执行某个操作。**

你当然可以每次手动做这些事，但那太麻烦了。Hook 让你"设置一次，自动执行"。

## Hook 的种类

Claude Code 支持多种 Hook 事件：

```
程序生命周期：
  Setup           → 程序启动时
  SessionStart    → 会话开始时
  SessionEnd      → 会话结束时

消息相关：
  UserPromptSubmit → 用户发送消息前

工具相关：
  PreToolUse      → 工具执行前
  PostToolUse     → 工具执行后

其他：
  CwdChanged      → 工作目录改变时
  FileChanged     → 文件被修改时
```

## 配置 Hook

Hook 在 `settings.json` 中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '即将执行 Bash 命令'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "FileEdit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write $CLAUDE_FILE_PATH"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/scripts/check_sensitive_info.py"
          }
        ]
      }
    ]
  }
}
```

### Hook 配置的结构

```typescript
{
  "matcher": "工具名",    // 可选：只对特定工具触发
  "hooks": [
    {
      "type": "command",   // Hook 类型（目前只支持 command）
      "command": "要执行的命令"
    }
  ]
}
```

## Hook 可以做什么？

### 1. 阻止操作

如果 Hook 脚本返回非零退出码，操作会被阻止：

```bash
#!/bin/bash
# check_before_push.sh
# 在 git push 之前运行测试

npm test
if [ $? -ne 0 ]; then
  echo "测试未通过，阻止 push"
  exit 1  # 非零退出码 → 阻止操作
fi
exit 0    # 零退出码 → 允许操作
```

### 2. 修改输入

Hook 可以修改工具的输入参数：

```bash
#!/bin/bash
# normalize_path.sh
# 把相对路径转换为绝对路径

# 读取输入（通过环境变量或 stdin）
INPUT_PATH="$CLAUDE_TOOL_INPUT_PATH"

# 转换为绝对路径
ABS_PATH=$(realpath "$INPUT_PATH")

# 输出修改后的输入（通过 stdout）
echo "{\"path\": \"$ABS_PATH\"}"
```

### 3. 添加上下文

Hook 可以向 AI 的上下文中注入额外信息：

```bash
#!/bin/bash
# add_context.sh
# 在每条消息前添加项目状态信息

echo "当前 Git 分支: $(git branch --show-current)"
echo "未提交的更改: $(git status --short | wc -l) 个文件"
echo "最近的提交: $(git log --oneline -1)"
```

这些信息会作为"系统提示"附加到消息中，帮助 AI 更好地理解当前状态。

### 4. 后处理

```bash
#!/bin/bash
# format_after_edit.sh
# 文件编辑后自动格式化

FILE_PATH="$CLAUDE_FILE_PATH"
EXTENSION="${FILE_PATH##*.}"

case "$EXTENSION" in
  ts|tsx|js|jsx)
    npx prettier --write "$FILE_PATH"
    ;;
  py)
    black "$FILE_PATH"
    ;;
  go)
    gofmt -w "$FILE_PATH"
    ;;
esac
```

## Hook 的执行流程

以 PreToolUse Hook 为例：

```
AI 请求使用 Bash 工具
    │
    ▼
检查是否有 PreToolUse Hook 匹配 "Bash"
    │
    ▼（如果有）
执行 Hook 脚本
    │
    ├── 退出码 = 0 → 继续执行工具
    ├── 退出码 ≠ 0 → 阻止工具执行
    └── 有输出 → 作为额外上下文添加
    │
    ▼
继续正常的权限检查流程
```

## Hook 的超时

Hook 不能无限运行：

```
工具相关的 Hook：最多 10 分钟
SessionEnd Hook：最多 1.5 秒
```

为什么 SessionEnd 只有 1.5 秒？因为用户要关闭程序，不能让 Hook 阻塞关闭过程。如果 Hook 超时，会被强制终止。

## 环境变量

Hook 脚本可以通过环境变量获取上下文信息：

```bash
$CLAUDE_SESSION_ID       # 当前会话 ID
$CLAUDE_TOOL_NAME        # 工具名称（PreToolUse/PostToolUse）
$CLAUDE_TOOL_INPUT       # 工具输入（JSON 格式）
$CLAUDE_FILE_PATH        # 文件路径（FileEdit/FileWrite）
$CLAUDE_WORKING_DIR      # 当前工作目录
```

## 实用 Hook 示例

### 示例 1：自动保存对话摘要

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [{
          "type": "command",
          "command": "echo \"Session $CLAUDE_SESSION_ID ended at $(date)\" >> ~/claude-sessions.log"
        }]
      }
    ]
  }
}
```

### 示例 2：禁止修改特定文件

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "FileEdit",
        "hooks": [{
          "type": "command",
          "command": "if echo $CLAUDE_TOOL_INPUT | grep -q 'package-lock.json'; then exit 1; fi"
        }]
      }
    ]
  }
}
```

### 示例 3：Git push 前检查

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "if echo $CLAUDE_TOOL_INPUT | grep -q 'git push'; then npm test || exit 1; fi"
        }]
      }
    ]
  }
}
```

## Hook vs 权限规则

你可能注意到 Hook 和权限规则有些重叠。它们的区别是：

| | 权限规则 | Hook |
|---|---|---|
| 复杂度 | 简单的匹配规则 | 可以运行任意脚本 |
| 能力 | 只能 allow/deny/ask | 可以修改输入、添加上下文、后处理 |
| 配置 | 模式字符串 | Shell 命令 |
| 适用场景 | 简单的黑白名单 | 复杂的业务逻辑 |

简单来说：权限规则是"简单的开关"，Hook 是"可编程的逻辑"。

## 本章小结

- **Hook** 在程序流程的特定点触发用户定义的脚本
- 支持多种事件：启动、会话、消息、工具执行前后
- Hook 可以：阻止操作、修改输入、添加上下文、后处理
- 有超时限制：工具 Hook 10 分钟，会话结束 Hook 1.5 秒
- 通过环境变量获取上下文信息

## Hook 的设计智慧

Hook 系统体现了一个重要的设计原则：**开放-封闭原则（Open-Closed Principle）**。

这个原则说的是：**软件应该对扩展开放，对修改封闭。**

什么意思？
- **对扩展开放**：你可以通过添加 Hook 来增加新行为
- **对修改封闭**：你不需要修改 Claude Code 的核心代码

不用 Hook 时：
```
想加"自动格式化"功能？
→ 修改 FileEditTool 的源代码
→ 可能引入 bug
→ 需要重新编译和部署
```

用 Hook 时：
```
想加"自动格式化"功能？
→ 在 settings.json 里加一个 PostToolUse Hook
→ 不修改任何源代码
→ 随时可以添加或删除
```

这就像给房子装修：你不需要拆墙（修改源代码），只需要挂画框（添加 Hook）。

下一章，我们将看看 Claude Code 如何与 IDE 编辑器集成。
