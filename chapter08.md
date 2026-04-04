# 第8章：与 AI 对话的秘密——消息系统

## 对话的本质

当你和 Claude 对话时，你觉得你们在"聊天"。但从程序的角度看，你们只是在互相传递**消息对象**。

每条消息都是一个数据结构：

```typescript
type Message = {
  id: string              // 唯一标识
  role: "user" | "assistant" | "system"  // 谁说的
  content: ContentBlock[] // 内容（可以是文字、图片、工具调用等）
  timestamp: number       // 时间戳
}
```

整个对话就是一个消息数组：

```typescript
const conversation = [
  { role: "user",      content: "帮我看看 index.ts" },
  { role: "assistant", content: "让我读取这个文件。", tool_use: {...} },
  { role: "user",      content: [{ type: "tool_result", ... }] },
  { role: "assistant", content: "这个文件的内容是..." },
]
```

注意：这里的 `role: "user"` 不一定是真的用户说的话。工具的执行结果也被包装成 `user` 角色的消息——因为 Claude API 的规则是：消息必须交替出现（user → assistant → user → assistant）。

## 消息的类型

Claude Code 内部使用的消息类型比 API 的更丰富：

```
Message 类型
├── UserMessage         — 用户输入的文字
├── AssistantMessage    — AI 的回复
├── SystemMessage       — 系统通知（成功、警告、错误）
├── AttachmentMessage   — 附件（Hook 输出、文件上下文、记忆）
├── ProgressMessage     — 工具执行进度
└── TombstoneMessage    — 删除标记（用于撤销/回退）
```

### UserMessage

```typescript
{
  role: "user",
  content: "帮我重构这段代码",
  // 可能还包含图片
  images: [{ id: "paste-1", data: "base64...", mimeType: "image/png" }],
}
```

### AssistantMessage

```typescript
{
  role: "assistant",
  content: [
    { type: "text", text: "让我看看这段代码..." },
    { type: "tool_use", id: "tool_1", name: "FileRead", input: { path: "src/app.ts" } },
  ],
  usage: {
    input_tokens: 1234,
    output_tokens: 567,
  },
}
```

AI 的回复可以包含多种内容：文字、工具调用、甚至"思考过程"。

### SystemMessage

```typescript
{
  role: "system",
  level: "success",  // 或 "warning" 或 "error"
  content: "文件已成功保存。",
}
```

这些是程序自己生成的消息，用来通知用户操作结果。

## 消息的处理流水线

一条用户消息从输入到最终显示，要经过一条长长的流水线：

```
用户按下回车
    │
    ▼
┌──────────────────────┐
│ 1. processUserInput  │
│                      │
│ ├── 展开粘贴内容     │  [Pasted text #1] → 实际内容
│ ├── 检测斜杠命令     │  /commit → 直接处理
│ ├── 执行提交钩子     │  运行用户定义的脚本
│ ├── 验证图片         │  检查格式和大小
│ └── 附加元数据       │  添加上下文信息
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 2. 消息标准化        │
│                      │
│ ├── 内部格式 → API 格式│  Message → MessageParam
│ ├── 添加缓存标记     │  cache_control
│ ├── 去重             │  删除重复的工具结果
│ └── 验证             │  检查图片大小/格式
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 3. 构建完整请求      │
│                      │
│ ├── 系统提示词       │  告诉 AI 它是谁
│ ├── 对话历史         │  之前的消息
│ ├── 工具定义         │  AI 可以用哪些工具
│ └── 参数配置         │  模型、温度等
└──────────┬───────────┘
           │
           ▼
     发送给 Claude API
```

### 第一步：processUserInput

这是消息处理的入口。它做的事情比你想象的多：

**展开粘贴内容**：当你粘贴一段文字时，Claude Code 会把它存储起来，用一个占位符 `[Pasted text #1]` 代替。发送前，它会把占位符替换回实际内容。

为什么要这样？因为粘贴的内容可能很长（比如一整个文件），直接显示在输入框里会影响体验。

**执行提交钩子**：用户可以配置"提交钩子"——在消息发送前自动运行的脚本。比如，你可以配置一个钩子来检查消息里有没有敏感信息。

### 第二步：消息标准化

Claude Code 的内部消息格式和 API 的消息格式不完全一样。标准化过程负责转换：

```typescript
// 内部格式（有很多额外字段）
{
  id: "msg-123",
  role: "user",
  content: "你好",
  timestamp: 1234567890,
  imagePasteIds: [...],
  toolUseResult: {...},
}

// API 格式（只保留 API 需要的字段）
{
  role: "user",
  content: [{ type: "text", text: "你好" }],
}
```

### 第三步：构建完整请求

最终发送给 API 的请求大约长这样：

```typescript
{
  model: "claude-sonnet-4-20250514",
  max_tokens: 8192,
  system: [
    {
      type: "text",
      text: "你是 Claude，运行在 Claude Code CLI 中...",
      cache_control: { type: "ephemeral" }
    }
  ],
  tools: [
    { name: "Bash", description: "...", input_schema: {...} },
    { name: "FileRead", description: "...", input_schema: {...} },
    // ... 更多工具
  ],
  messages: [
    { role: "user", content: "帮我看看 index.ts" },
    // ... 对话历史
  ],
}
```

## 系统提示词——AI 的"说明书"

每次发消息给 AI 时，都会附带一个"系统提示词"。这就像给 AI 一份说明书，告诉它：

1. **你是谁**："你是 Claude，运行在 Claude Code CLI 中"
2. **你能做什么**："你有以下工具可用：Bash、FileRead、FileEdit..."
3. **你应该怎么做**："优先使用专用工具而不是 Bash"
4. **你不应该做什么**："不要执行危险操作"

系统提示词的构建也经过了精心优化。它被分成几个部分：

```typescript
systemPrompt = [
  // 第一部分：归属标记（用于计费追踪）
  // 不缓存，因为每个用户不同

  // 第二部分：CLI 前缀（通用描述）
  // 缓存范围：组织级别（同一组织的用户共享缓存）

  // 第三部分：默认提示词（工具列表、行为规则）
  // 缓存范围：全局（所有用户共享）

  // 第四部分：用户自定义指令
  // 不缓存，因为每个用户不同
]
```

为什么要分层缓存？因为系统提示词很长（可能有几千个 token），每次都发送很浪费。通过缓存，第二次对话时 API 可以直接使用缓存的提示词，节省了约 **90%** 的 token 费用。

## 对话历史管理

随着对话进行，消息越来越多。Claude Code 需要管理这个不断增长的列表：

### 消息的存储

```
内存中：messages[]
  → 用于当前对话的实时交互

磁盘上：~/.claude/sessions/<id>/transcript.jsonl
  → 用于恢复会话、历史查询
```

`transcript.jsonl` 是一种叫 "JSON Lines" 的格式——每行一个 JSON 对象。这种格式的好处是可以**追加写入**，不需要每次都重写整个文件。

### 自动压缩

当对话太长时，Claude Code 会自动压缩：

```
检测 token 使用量
    │
    ▼
如果 > 上下文窗口的 90%
    │
    ▼
触发自动压缩
    │
    ▼
1. 保留最近几条消息
2. 让 AI 总结更早的消息
3. 用总结替换旧消息
4. 插入一个"压缩边界标记"
```

压缩后的消息看起来像这样：

```typescript
[
  {
    role: "system",
    type: "compact_boundary",
    content: "以下是之前对话的摘要：用户正在开发一个 React 应用..."
  },
  // ... 最近的几条消息（未被压缩）
]
```

## 工具调用的消息流

当 AI 想使用一个工具时，消息的流动变得更复杂。让我们看一个完整的例子：

```
第 1 轮：用户发消息
messages = [
  { role: "user", content: "帮我读取 index.ts" }
]

第 2 轮：AI 回复（包含工具调用）
messages = [
  { role: "user", content: "帮我读取 index.ts" },
  { role: "assistant", content: [
    { type: "text", text: "让我读取这个文件。" },
    { type: "tool_use", id: "t1", name: "FileRead", input: { path: "index.ts" } }
  ]}
]

第 3 轮：工具结果（作为 user 消息）
messages = [
  { role: "user", content: "帮我读取 index.ts" },
  { role: "assistant", content: [
    { type: "text", text: "让我读取这个文件。" },
    { type: "tool_use", id: "t1", name: "FileRead", input: { path: "index.ts" } }
  ]},
  { role: "user", content: [
    { type: "tool_result", tool_use_id: "t1", content: "// index.ts 的内容..." }
  ]}
]

第 4 轮：AI 基于工具结果继续回复
messages = [
  ...,  // 前面的消息
  { role: "assistant", content: "这个文件包含了应用的入口点..." }
]
```

注意：工具结果被包装成 `user` 角色的消息。从 API 的角度看，"对话"其实是这样的：

```
user     → "帮我读取 index.ts"
assistant → "让我用 FileRead" + [工具调用]
user     → [工具结果: 文件内容]
assistant → "这个文件包含了..."
```

严格交替的 user/assistant 格式是 Claude API 的要求。

## 大结果的处理

有时候工具返回的结果很大（比如读取一个 10 万行的文件）。直接放在消息里会占用太多 token。Claude Code 有一个聪明的处理方式：

```typescript
const MAX_RESULT_SIZE = 500_000  // 50 万字符

if (toolResult.length > MAX_RESULT_SIZE) {
  // 1. 把完整结果保存到磁盘
  const filePath = saveToTempFile(toolResult)

  // 2. 只发送预览 + 文件路径给 AI
  return {
    content: `结果太大（${toolResult.length} 字符），已保存到 ${filePath}。
              以下是前 1000 字符的预览：
              ${toolResult.slice(0, 1000)}...`
  }
}
```

这就像你找人帮忙查资料，结果发现资料有 100 页。你不会把 100 页都念给他听——你会说"资料放在这个文件夹里，我先给你说说大概内容"。

## 本章小结

- 对话本质上是一个消息对象数组，严格按 user/assistant 交替排列
- 消息从用户输入到发送给 API 要经过：处理 → 标准化 → 构建请求
- 系统提示词分层缓存，节省约 90% 的 token 费用
- 对话历史自动压缩，避免超出上下文窗口限制
- 工具结果被包装成 user 角色消息
- 大结果保存到磁盘，只发送预览给 AI

## 思考题

1. 为什么 API 要求消息必须 user/assistant 交替？（提示：想想 AI 的训练方式）
2. 如果自动压缩的摘要遗漏了重要信息怎么办？这个问题有完美的解决方案吗？
3. 除了保存到磁盘，处理大结果还有什么方式？

## 消息系统的设计启示

Claude Code 的消息系统给我们展示了一个重要的工程原则：**内部表示和外部接口可以不同。**

内部消息（Message）有很多额外字段：ID、时间戳、图片 ID、工具结果引用……这些是程序管理对话时需要的。

外部消息（MessageParam）只有 API 需要的字段：role 和 content。

在两者之间有一层"翻译"（标准化）。这样的好处是：
- 内部可以自由添加字段，不影响 API 调用
- API 格式变了，只需要改翻译层，不影响内部逻辑
- 不同的"外部"（API、日志、会话存档）可以有不同的翻译

这就是**适配器模式**——在两个不兼容的系统之间放一个"翻译官"。你以后在设计系统时，如果发现两个部分的数据格式不一致，不要强迫它们统一，而是加一个翻译层。

下一章，我们将深入查询引擎——整个程序的"大脑中枢"。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
