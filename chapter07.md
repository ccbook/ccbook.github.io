# 第7章：命令系统——斜杠的魔法

## 斜杠命令是什么？

在 Claude Code 的对话中，你可以输入以 `/` 开头的特殊命令：

```
/commit          ← 创建 Git 提交
/compact         ← 压缩对话历史
/review          ← 代码审查
/theme dark      ← 切换到深色主题
/help            ← 显示帮助信息
```

这些命令不会被发送给 AI，而是直接由程序处理。它们就像游戏里的"作弊码"——一种快速触发特定功能的方式。

## 命令的注册中心

所有斜杠命令在 `commands.ts`（约 25,000 行）中注册。每个命令都有统一的结构：

```typescript
type Command = {
  name: string          // 命令名，如 "commit"
  help: string          // 帮助文本
  aliases?: string[]    // 别名，如 ["ci"] 是 "commit" 的别名
  priority?: number     // 在命令列表中的排序
  isVisible?: boolean   // 是否在帮助中显示

  handler(input: string, context: CommandContext): void
  // 处理函数：接收用户输入的参数，执行命令

  shouldHighlightInCommandPalette?: (context: CommandContext) => boolean
  // 是否在命令面板中高亮（推荐给用户）
}
```

看到了吗？每个命令都遵循同一个"模板"。这就是**接口**的力量——只要你按照模板来写，你的命令就能无缝融入系统。

## 命令的分类

Claude Code 有 50 多个斜杠命令，我们可以分成几大类：

### 对话控制类

| 命令 | 作用 | 示例 |
|------|------|------|
| `/compact` | 压缩对话历史，释放 token 空间 | `/compact` |
| `/context` | 查看当前的 token 使用情况 | `/context` |
| `/clear` | 清空当前对话 | `/clear` |
| `/resume` | 恢复之前的会话 | `/resume` |

### 开发工具类

| 命令 | 作用 | 示例 |
|------|------|------|
| `/commit` | 创建 Git 提交 | `/commit` |
| `/review` | 代码审查 | `/review PR_URL` |
| `/diff` | 查看代码差异 | `/diff` |
| `/doctor` | 诊断环境问题 | `/doctor` |

### 设置类

| 命令 | 作用 | 示例 |
|------|------|------|
| `/config` | 编辑配置 | `/config` |
| `/theme` | 切换主题 | `/theme light` |
| `/vim` | 切换 Vim 模式 | `/vim` |

### 系统类

| 命令 | 作用 | 示例 |
|------|------|------|
| `/login` | 登录 | `/login` |
| `/logout` | 登出 | `/logout` |
| `/cost` | 查看费用 | `/cost` |
| `/help` | 帮助 | `/help` |

## 命令的解析流程

当你输入 `/commit -m "修复 bug"` 时，发生了什么？

```
用户输入: "/commit -m 修复 bug"
    │
    ▼
1. 检测到以 "/" 开头
   → 这是一个斜杠命令，不是普通消息
    │
    ▼
2. 提取命令名: "commit"
   提取参数: "-m 修复 bug"
    │
    ▼
3. 在命令注册表中查找 "commit"
   → 找到了！CommitCommand
    │
    ▼
4. 检查别名
   如果输入是 "/ci"，也会匹配到 CommitCommand
   （因为 "ci" 是它的别名）
    │
    ▼
5. 调用 handler
   CommitCommand.handler("-m 修复 bug", context)
    │
    ▼
6. handler 执行具体逻辑
   → 查看 git 状态
   → 生成提交信息
   → 执行 git commit
```

## 深入一个命令：/compact

让我们详细看看 `/compact` 命令的实现，因为它揭示了一个有趣的问题——**上下文窗口的限制**。

### 问题：AI 的"短期记忆"

AI 模型有一个叫"上下文窗口"的限制——它一次能"看到"的文本量是有限的。就像你的工作台空间有限，放太多东西就放不下了。

当你和 Claude 对话很久之后，消息越来越多，token 数（可以理解为"文字数"）越来越大。最终会接近上下文窗口的上限。

### 解决方案：压缩

`/compact` 命令的做法很聪明——它让 AI 总结之前的对话：

```typescript
// 简化的 /compact 实现逻辑
async function compactHandler(input, context) {
  const messages = context.getMessages()

  // 1. 找到可以压缩的旧消息
  const oldMessages = messages.slice(0, -5)  // 保留最近 5 条
  const recentMessages = messages.slice(-5)

  // 2. 让 AI 总结旧消息
  const summary = await claude.summarize(oldMessages)
  // 例如："用户在开发一个 React 应用，已经完成了登录页面，
  //        正在处理数据获取的 bug。"

  // 3. 用总结替换旧消息
  context.setMessages([
    { role: "system", content: `之前的对话摘要：${summary}` },
    ...recentMessages,
  ])

  // 4. 通知用户
  console.log(`已压缩 ${oldMessages.length} 条消息，释放了 ${savedTokens} tokens`)
}
```

这就像做读书笔记：你不需要记住书的每个字，只需要记住关键点。AI 把长长的对话"浓缩"成一段摘要，腾出空间来继续对话。

## 命令的条件注册

不是所有命令在所有情况下都可用。有些命令需要特定条件才会出现：

```typescript
export function getAllCommands(): Command[] {
  return [
    // 基础命令，总是可用
    HelpCommand,
    CompactCommand,
    ClearCommand,

    // 需要 Git 环境
    ...(isGitRepo() ? [CommitCommand, DiffCommand] : []),

    // 需要特定功能开关
    ...(feature('VOICE_MODE') ? [VoiceCommand] : []),

    // 需要登录
    ...(isAuthenticated() ? [ShareCommand] : []),
  ]
}
```

这就像一个游戏：你需要解锁特定成就才能使用某些技能。没有 Git 仓库就没有 `/commit`，没有登录就没有 `/share`。

## 命令面板

当你输入 `/` 但还没输入完命令名时，Claude Code 会显示一个**命令面板**——列出所有可用命令供你选择：

```
┌─ Commands ────────────────────────────┐
│  /commit    Create a git commit        │
│  /compact   Compress conversation      │
│  /config    Edit settings              │
│  /context   View token usage           │
│  /diff      View code changes          │
│  /doctor    Diagnose issues            │
│  /help      Show help                  │
│  /review    Review code changes        │
│  /theme     Switch theme               │
└────────────────────────────────────────┘
```

随着你继续输入，列表会实时过滤：

```
输入: /co

┌─ Commands ────────────────────────────┐
│  /commit    Create a git commit        │  ← 匹配 "co"
│  /compact   Compress conversation      │  ← 匹配 "co"
│  /config    Edit settings              │  ← 匹配 "co"
│  /context   View token usage           │  ← 匹配 "co"
│  /cost      View usage costs           │  ← 匹配 "co"
└────────────────────────────────────────┘
```

这种实时过滤是怎么实现的？

```typescript
function filterCommands(input: string, commands: Command[]): Command[] {
  const query = input.toLowerCase()
  return commands
    .filter(cmd => cmd.name.toLowerCase().startsWith(query))
    .sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0))
}
```

就是简单的字符串匹配 + 排序。有时候简单的方案就是最好的方案。

## 自己写一个命令

理解了命令系统后，让我们想象一下怎么写一个新命令。假设我们要写一个 `/weather` 命令，显示天气信息：

```typescript
const WeatherCommand: Command = {
  name: "weather",
  help: "显示当前天气",
  aliases: ["w"],

  async handler(input, context) {
    const city = input || "Beijing"

    // 调用天气 API
    const weather = await fetchWeather(city)

    // 显示结果
    context.displayMessage({
      role: "system",
      content: `${city} 的天气：${weather.temperature}°C, ${weather.description}`,
    })
  },
}
```

然后只需要在 `getAllCommands()` 里加一行：

```typescript
export function getAllCommands(): Command[] {
  return [
    // ... 其他命令
    WeatherCommand,  // 新增
  ]
}
```

就这么简单！这就是好的架构设计的力量——添加新功能只需要两步：实现接口 + 注册。不需要修改其他任何代码。

## 命令 vs 工具

你可能会困惑：命令和工具有什么区别？

| | 命令 | 工具 |
|---|---|---|
| 触发者 | 用户输入 `/xxx` | AI 决定使用 |
| 执行者 | 程序直接执行 | AI 请求后程序执行 |
| 权限 | 不需要权限检查 | 需要权限检查 |
| 示例 | `/commit`, `/theme` | Bash, FileRead |

简单来说：**命令是用户的快捷操作，工具是 AI 的能力扩展。**

## 本章小结

- 斜杠命令是以 `/` 开头的特殊命令，由程序直接处理
- 每个命令遵循统一的接口（name、help、handler 等）
- 命令可以条件注册——根据环境决定哪些命令可用
- `/compact` 命令通过让 AI 总结旧对话来释放 token 空间
- 命令面板提供实时过滤和搜索
- 好的架构让添加新命令只需两步：实现 + 注册
- 命令由用户触发，工具由 AI 触发——这是核心区别

## 设计启示：接口即契约

命令系统最值得学习的设计思想是**接口即契约**。

`Command` 接口定义了"一个命令应该是什么样的"，这就是一份"契约"。只要你遵守这份契约（提供 name、help、handler），你的代码就能融入系统。

这个原则在现实世界中也很常见：
- **USB 接口**是一份契约：任何遵守 USB 协议的设备都能连接电脑
- **法律格式**是一份契约：任何按格式填写的合同都能被法律认可
- **考试大纲**是一份契约：只要覆盖大纲内容，任何教材都能用

当你将来设计系统时，先定义好接口（契约），再实现具体功能。这样其他人（或者你未来的自己）就知道怎么扩展你的系统。

下一章，我们将进入对话引擎篇，深入了解消息系统的工作原理。
