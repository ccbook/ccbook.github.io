# 第11章：上下文管理——有限的记忆

## AI 的记忆问题

人类的对话是连续的——你和朋友聊天，你们都能记住之前说过什么。但 AI 的"记忆"是有限的。

每次 AI 生成回复时，它需要"看到"整个对话历史。而它能看到的文本量是有限的——这就是**上下文窗口（Context Window）**。

不同的模型有不同的上下文窗口大小：

| 模型 | 上下文窗口 |
|------|-----------|
| Claude Sonnet | ~200,000 tokens |
| Claude Opus | ~1,000,000 tokens |

1 个 token 大约是 4 个英文字符或 1.5 个中文字符。所以 200,000 tokens 大约是 80 万个英文字符——看起来很多，但在一个长对话中，加上系统提示词、工具定义、工具返回的大段代码，token 消耗得很快。

## Token 的组成

让我们看看一次 API 请求中 token 是怎么分配的：

```
┌────────────────────────────────┐
│ 系统提示词        ~5,000 tokens │  ← AI 的"说明书"
├────────────────────────────────┤
│ 工具定义          ~8,000 tokens │  ← 40+ 工具的描���
├────────────────────────────────┤
│ CLAUDE.md 记忆    ~2,000 tokens │  ← 项目记忆文件
├────────────────────────────────┤
│ 对话历史         ~50,000 tokens │  ← 所有消息
├────────────────────────────────┤
│ 本次用户输入        ~500 tokens │  ← 你问的问题
├────────────────────────────────┤
│ ═══ 可用于回复 ════════════════│
│ AI 输出空间      ~8,000 tokens  │  ← AI 的回复
└────────────────��───────────────┘
总计: ~73,500 tokens
```

看到了吗？光是"固定开销"（系统提示词 + 工具定义 + 记忆）就要 15,000 tokens。真正留给对话的空间没有想象的那么多。

## 提示缓存：省钱的秘密

Claude Code 的一个关键优化是**提示缓存（Prompt Caching）**。

每次 API 请求都要发送系统提示词和工具定义——这些内容大部分是不变的。如果每次都当作新内容处理，就要重复付费。

提示缓存的工作方式：

```typescript
// 第一次请求：完整发送，创建缓存
{
  system: [{
    type: "text",
    text: "你是 Claude，运行在 Claude Code CLI 中...",
    cache_control: { type: "ephemeral" }  // 请求缓存
  }]
}
// 费用：完整价格 + 缓存创建费用

// 后续请求：使用缓存
// API 自动检测到内容没变，使用缓存
// 费用：仅缓存读取费用（约为完整价格的 10%）
```

结果：**后续请求节省约 90% 的 token 费用**。

Claude Code 把系统提示词分成多层，最大化缓存命中率：

```
静态内容（全局缓存，所有用户共享）
  "你是 Claude，一个 AI 助手..."
  ↓
组织级内容（同组织用��共享）
  "以下工具可用：Bash, FileRead..."
  ↓
用户级内容（不缓存，每个用户不同）
  "当前项目：/Users/alice/myapp"
```

## 压缩策略

当对话接近上下文窗口上限时，Claude Code 有几种压缩策略：

### 策略一：手动压缩（/compact）

用户主动输入 `/compact` 命令，触发对话压缩。

### 策略二：自动压缩

```typescript
// 每次 API 调用前检查
if (tokenCount > contextWindowSize * 0.9) {
  // 触发自动压缩
  await partialCompactConversation(messages)
}
```

### 策略三：部分压缩

不是压缩所有旧消息，而是只压缩最老的一批：

```
压缩前：
  [消息1] [消息2] [消息3] [消息4] [消息5] [消息6] [消息7]

部分压缩后：
  [消息1-4的摘要] [消息5] [消息6] [消息7]
```

这样保留了最近的详细对话，同时释放了旧消息占用的空间。

### 策略四：大结果持久化

当工具返回的结果太大时，存到磁盘而不是保留在消息里：

```typescript
if (toolResult.length > 500_000) {  // 超过 50 万字符
  // 保存到临时文件
  const path = "~/.claude/tool-results/result-abc.txt"
  writeFile(path, toolResult)

  // 只在消息里保留摘要
  return `[结果已保存到 ${path}，共 ${toolResult.length} 字符]
          前 1000 字符预览：${toolResult.slice(0, 1000)}...`
}
```

## Token 估算 vs 精确计算

计算 token 数量有两种方式：

**估算**（快，但不精确）：
```typescript
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)  // 经验公式
}
// 速度：<1ms
```

**精确计算**（慢，需要 API 调用）：
```typescript
async function exactTokenCount(messages): Promise<number> {
  const response = await anthropic.messages.countTokens({
    messages: messages
  })
  return response.input_tokens
}
// 速度：~100ms（网络延迟）
```

Claude Code 的策略是**平时估算，关键时刻精确计算**：

```typescript
const estimated = estimateTokens(allContent)

if (estimated < contextWindow * 0.7) {
  // 离上限还远，用估算值就好
  return estimated
}

if (estimated > contextWindow * 0.85) {
  // 接近上限了，需要精确值来做决策
  return await exactTokenCount(messages)
}
```

这就像你开车看油表：平时看一眼大概就知道够不够用，快没油的时候才需要精确到升。

## 上下文的"保鲜"问题

压缩对话时有一个两难的问题：**压缩得太多会丢失信息，压缩得太少释放不了空间。**

比如这段对话：

```
用户: 帮我看看 database.ts 有什么问题
AI: 我发现第 42 行有一个 SQL 注入漏洞...
用户: 帮我修复它
AI: 好的，我已经修改了第 42 行...
```

如果压缩成：

```
摘要：用户让 AI 看了 database.ts，AI 修复了一个问题。
```

关键信息丢失了：是什么问题？修复了哪一行？如果用户后续问"你刚才修复的那个漏洞，还需要做其他检查吗？"，AI 就无法给出好的回答。

Claude Code 的压缩会让 AI 来做摘要，因为 AI 最擅长判断哪些信息是重要的：

```typescript
const summaryPrompt = `
请总结以下对话的关键信息，包括：
- 用户的目标是什么
- 做了哪些修改（包括具体的文件名和行号）
- 当前的工作状态
- 任何重要的决策或发现

对话内容：
${messagesText}
`
const summary = await claude.messages.create({
  messages: [{ role: "user", content: summaryPrompt }],
  max_tokens: 500,
})
```

## 上下文窗口的可视化

Claude Code 有一个 `/context` 命令，可以可视化当前的 token 使用情况：

```
$ /context

Token Usage Breakdown:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━��━━━━━━
System prompt:    ████░░░░░░░░░░░░  5,120 (7%)
Tool definitions: ██████░░░░░░░���░░  8,340 (11%)
Memory files:     ██░░░░░░░░░░░░░░  2,100 (3%)
Conversation:     ████████████████ 52,000 (69%)
Available:        ████░░░░░░░░░░░░  7,440 (10%)
━━━━━���━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 75,000 / 200,000 tokens (38%)

Cache status:
  System prompt: CACHED (saving ~$0.02/request)
  Tool schemas:  CACHED (saving ~$0.03/request)
```

这让用户清楚地看到 token 是怎么使用的，以及还有多少空间。

## 本章小结

- AI 的上下文窗口是有限的（200K - 1M tokens）
- "固定开销"（系统提示词 + 工具定义）就要消耗约 15K tokens
- **提示缓存**节省约 90% 的重复 token 费用
- 压缩策略：手动、自动、部分压缩、大结果持久化
- Token 计算：平时估算（快），关键时刻精确计算（准）
- 压缩的两难：信息保留 vs 空间释放
- `/context` 命令可视化 token 使用

## 思考题

1. 如果你在写一个对话 AI，上下文窗口只有 4,000 tokens（很小），你会怎么设计压缩策略？
2. 提示缓存为什么要分成全局、组织、用户三层？只有一层不行吗？
3. 有没有办法完全解决"压缩丢失信息"的问题？（提示：想想人类是怎么做笔记的）

## 一个有趣的数学问题

假设你和 AI 进行了 100 轮对话，每轮平均 500 tokens。上下文窗口是 200,000 tokens。

```
固定开销：15,000 tokens（系统提示词 + 工具定义）
对话内容：100 × 500 = 50,000 tokens
总计：65,000 tokens

剩余空间：200,000 - 65,000 = 135,000 tokens（68% 剩余）
```

看起来还很充裕。但如果有些轮次涉及大文件（比如 AI 读了一个 5,000 行的文件，约 20,000 tokens），情况就不一样了：

```
固定开销：15,000 tokens
对话内容：50,000 tokens
3 次大文件读取：3 × 20,000 = 60,000 tokens
总计：125,000 tokens

剩余空间：200,000 - 125,000 = 75,000 tokens（37% 剩余）
```

只读了 3 个大文件，可用空间就减少了一半！

这就是为什么上下文管理如此重要——大文件读取是 token 消耗的"大户"。理解这一点，你就明白了为什么 FileRead 有行数限制、为什么大结果要保存到磁盘。

下一章，我们将进入工具系统篇——Claude Code 最强大的能力来源。
