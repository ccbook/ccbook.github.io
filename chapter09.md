# 第9章：查询引擎——大脑中枢

## 程序中最复杂的部分

如果 Claude Code 有一个"大脑"，那就是查询引擎。它由两个核心文件组成：

- `query.ts`（约 68,000 行）—— 查询管道，处理消息流
- `QueryEngine.ts`（约 46,000 行）—— API 调用和工具执行循环

这两个文件加起来超过 11 万行代码，是整个项目中最庞大的部分。别被数字吓到——我们会把它拆解成容易理解的小块。

## 核心循环：Agent Loop

查询引擎的核心是一个**循环**。是的，一个看似简单的 `while` 循环支撑了整个 AI 助手的运作：

```typescript
// 大幅简化的核心循环
async function queryLoop(messages, tools) {
  while (true) {
    // 1. 发送消息给 AI，获取回复
    const response = await callClaudeAPI(messages, tools)

    // 2. 把 AI 的回复加入消息列表
    messages.push({ role: "assistant", content: response.content })

    // 3. 检查 AI 是否使用了工具
    const toolUses = response.content.filter(block => block.type === "tool_use")

    if (toolUses.length === 0) {
      // AI 没有使用工具，对话结束
      break
    }

    // 4. 执行所有工具，收集结果
    const toolResults = await executeTools(toolUses)

    // 5. 把工具结果加入消息列表
    messages.push({ role: "user", content: toolResults })

    // 6. 回到第 1 步，让 AI 继续
  }
}
```

每一"圈"循环就是一个**轮次（turn）**。一次用户输入可能触发多个轮次：

```
用户: "帮我创建一个 React 组件并测试"

轮次 1: AI → "好的，让我先创建组件文件"
         工具 → FileWrite("src/Button.tsx", "...")
         结果 → "文件已创建"

轮次 2: AI → "现在让我创建测试文件"
         工具 → FileWrite("src/Button.test.tsx", "...")
         结果 → "文件已创建"

轮次 3: AI → "让我运行测试"
         工具 → Bash("npm test Button.test.tsx")
         结果 → "3 tests passed"

轮次 4: AI → "组件已创建并通过了所有测试。"
         没有工具调用 → 循环结束
```

这个循环就是 **Agent Loop**（智能体循环），是所有 AI Agent 的核心模式。AI 不断地"思考 → 行动 → 观察 → 再思考"，直到任务完成。

## 发送 API 请求

每个轮次的第一步是调用 Claude API。让我们看看请求是怎么构建的：

```typescript
const response = await anthropic.messages.stream({
  model: "claude-sonnet-4-20250514",
  max_tokens: 8192,
  system: systemPrompt,
  tools: toolSchemas,
  messages: normalizedMessages,
  // 性能优化：使用 beta 特性
  betas: ["prompt_caching_2025"]
})
```

参数解释：

| 参数 | 作用 |
|------|------|
| `model` | 使用哪个 AI 模型 |
| `max_tokens` | AI 最多回复多少 token |
| `system` | 系统提示词（AI 的"说明书"） |
| `tools` | 可用工具列表（告诉 AI 它有什么能力） |
| `messages` | 对话历史 |
| `betas` | 启用的 beta 特性（如提示缓存） |

### 流式响应

注意我们用的是 `messages.stream()` 而不是 `messages.create()`。区别是：

- `create()` —— 等 AI 写完整个回复后一次性返回
- `stream()` —— AI 每写一个字就立刻发过来

就像看一部电影：`create()` 是等整部电影下载完再看，`stream()` 是边下载边看（在线流播放）。

流式响应让用户能**实时看到 AI 的回复**，不用傻等几十秒。

## 流式事件处理

流式响应传回来的不是完整的消息，而是一个个"事件"：

```typescript
async function* handleStream(stream) {
  for await (const event of stream) {
    switch (event.type) {
      case "content_block_start":
        // 一个新的内容块开始了（文字 or 工具调用）
        yield { type: "block_start", blockType: event.content_block.type }
        break

      case "content_block_delta":
        // 收到一小段增量内容
        if (event.delta.type === "text_delta") {
          yield { type: "text", text: event.delta.text }
          // → 界面上显示这几个字
        }
        if (event.delta.type === "input_json_delta") {
          yield { type: "tool_input", json: event.delta.partial_json }
          // → 工具的输入参数正在逐步到来
        }
        break

      case "message_stop":
        // AI 回复结束
        yield { type: "done", usage: event.usage }
        break
    }
  }
}
```

`function*` 和 `yield` 是**生成器**语法。你可以把它想象成一个"水龙头"——每次调用 `next()` 就流出一滴水（一个事件），而不是一次性倒出整桶水。

## 工具执行：串行与并行

当 AI 在一个回复中使用了多个工具时，Claude Code 需要决定：是一个一个执行，还是同时执行？

```typescript
// AI 的回复可能包含多个工具调用
[
  { type: "tool_use", name: "FileRead", input: { path: "a.ts" } },
  { type: "tool_use", name: "FileRead", input: { path: "b.ts" } },
  { type: "tool_use", name: "FileWrite", input: { path: "c.ts", content: "..." } },
]
```

规则是：

```
读操作可以并行（同时执行）
写操作必须串行（一个一个执行）
```

为什么？因为两个"读文件"操作互不影响，可以同时进行，加快速度。但两个"写文件"操作可能互相冲突——如果它们写同一个文件，先后顺序就很重要。

具体实现使用了**批次分区**的策略：

```
工具调用列表:
  [Read a.ts] [Read b.ts] [Write c.ts] [Read d.ts]

分成批次:
  批次 1: [Read a.ts, Read b.ts]  → 并行执行（都是只读）
  批次 2: [Write c.ts]            → 单独执行（写操作）
  批次 3: [Read d.ts]             → 单独执行（在写之后）

执行:
  批次 1 ─┬─ Read a.ts ──→ 结果
          └─ Read b.ts ──→ 结果
  批次 2 ─── Write c.ts ─→ 结果
  批次 3 ─── Read d.ts ──→ 结果
```

## 错误处理与重试

网络请求总会出错。Claude Code 的重试策略很精细：

```typescript
async function withRetry(operation, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
    try {
      return await operation()
    } catch (error) {
      if (error.status === 401) {
        // 认证失败 → 刷新 token 后重试
        await refreshOAuthToken()
        continue
      }

      if (error.status === 429 || error.status === 529) {
        // 速率限制 → 等待后重试
        const waitTime = getRetryAfterMs(error)
        await sleep(waitTime)
        continue
      }

      if (error.status >= 500) {
        // 服务器错误 → 指数退避重试
        await sleep(Math.min(2000 * 2 ** attempt, 120000))
        continue
      }

      // 其他错误 → 不重试，直接报错
      throw error
    }
  }
}
```

**指数退避**是一种经典的重试策略：第一次等 2 秒，第二次等 4 秒，第三次等 8 秒……每次等待时间翻倍。这避免了"所有人同时重试导致服务器更忙"的问题。

```
重试 1: 等待 2 秒
重试 2: 等待 4 秒
重试 3: 等待 8 秒
重试 4: 等待 16 秒
...
最长: 等待 120 秒
```

## Token 预算管理

AI 模型的"记忆"（上下文窗口）是有限的。Claude Code 需要精细地管理 token 使用：

```typescript
function checkTokenBudget(messages, maxContextTokens) {
  const estimatedTokens = estimateTokenCount(messages)

  if (estimatedTokens > maxContextTokens * 0.9) {
    // 使用了 90% 以上 → 警告
    warn("接近 token 上限，建议使用 /compact 压缩对话")
  }

  if (estimatedTokens > maxContextTokens) {
    // 超过上限 → 自动压缩
    return autoCompact(messages)
  }

  return messages
}
```

**Token 计数的估算**：精确计算 token 数需要调用 API（慢），所以平时用估算：

```typescript
function estimateTokenCount(text: string): number {
  // 经验公式：大约 4 个字符 = 1 个 token（对英文）
  // 中文大约 1.5 个字符 = 1 个 token
  return Math.ceil(text.length / 4)
}
```

只有当估算值接近上限时，才会调用 API 获取精确数值。这是一个**惰性精确计算**的优化策略——"大部分时候粗略估计就够了，只在关键时刻才精确计算。"

## 查询引擎的完整流程图

让我们把所有部分串起来：

```
                    用户输入
                       │
                       ▼
              ┌─────────────────┐
              │ processUserInput│
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  检查 token 预算 │
              └────────┬────────┘
                       │
          ┌────────────┤
          │            ▼ (如果超预算)
          │   ┌─────────────────┐
          │   │  自动压缩对话    │
          │   └────────┬────────┘
          │            │
          └────────────┤
                       │
                       ▼
     ┌────────── Agent Loop ─────────┐
     │                                │
     │  ┌─────────────────────────┐   │
     │  │ 构建 API 请求            │   │
     │  │ (系统提示词+消息+工具)    │   │
     │  └────────────┬────────────┘   │
     │               │                │
     │               ▼                │
     │  ┌─────────────────────────┐   │
     │  │ 调用 Claude API (流式)   │   │
     │  │ ← 重试 + 指数退避       │   │
     │  └────────────┬────────────┘   │
     │               │                │
     │               ▼                │
     │  ┌─────────────────────────┐   │
     │  │ 处理流式响应             │   │
     │  │ → 实时显示文字           │   │
     │  │ → 收集工具调用           │   │
     │  └────────────┬────────────┘   │
     │               │                │
     │        有工具调用？             │
     │           ╱     ╲              │
     │         是       否            │
     │         ╱         ╲            │
     │        ▼           ▼           │
     │  ┌──────────┐  结束循环        │
     │  │ 权限检查  │                  │
     │  └────┬─────┘                  │
     │       │                        │
     │       ▼                        │
     │  ┌──────────┐                  │
     │  │ 执行工具  │                  │
     │  │(串行/并行)│                  │
     │  └────┬─────┘                  │
     │       │                        │
     │       ▼                        │
     │  工具结果加入消息               │
     │       │                        │
     │       └──── 回到循环顶部 ──────│
     │                                │
     └────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ 保存到会话记录   │
              │ 记录指标和费用   │
              │ 运行后处理钩子   │
              └─────────────────┘
```

## Stop Reason：循环为什么结束？

Claude API 的每个回复都带有一个 `stop_reason`，告诉我们 AI 为什么停下来：

| stop_reason | 含义 | 查询引擎的反应 |
|-------------|------|---------------|
| `end_turn` | AI 说完了 | 结束循环 |
| `tool_use` | AI 想用工具 | 执行工具，继续循环 |
| `max_tokens` | 达到输出上限 | 尝试压缩或增加上限 |

当 `stop_reason` 是 `max_tokens` 时，说明 AI 的回复被截断了——它还没说完就被强制停止。这时查询引擎会尝试恢复：

```typescript
if (response.stop_reason === "max_tokens") {
  if (recoveryCount < 3) {
    // 尝试 1：压缩对话，腾出空间
    await autoCompact(messages)
    recoveryCount++
    continue  // 重试
  } else {
    // 恢复失败，通知用户
    warn("AI 的回复被截断。请尝试简化你的问题。")
    break
  }
}
```

## 本章小结

- **Agent Loop** 是查询引擎的核心——"思考 → 行动 → 观察 → 再思考"的循环
- 每个轮次包含：API 调用 → 流式处理 → 工具执行
- 流式响应让用户实时看到 AI 的回复
- 工具按读写属性分批：读并行、写串行
- 指数退避策略处理网络错误和速率限制
- Token 预算管理：估算 + 惰性精确计算 + 自动压缩
- `stop_reason` 决定循环继续还是结束

## 思考题

1. 为什么 Agent Loop 不能无限循环？有什么风险？（提示：费用、时间、无限循环）
2. 如果 AI 在一个回复里同时读一个文件又写另一个文件，执行顺序应该是什么？
3. 指数退避的最大等待时间为什么要封顶在 120 秒？如果不封顶会怎样？

## 延伸思考：Agent Loop 的哲学

Agent Loop 不仅是一种编程模式，它还反映了一种解决问题的哲学：

**"不要试图一步到位，而是通过不断迭代来逼近目标。"**

想想你写作文的过程：
1. 先写一个初稿（思考）
2. 重读一遍，发现一些问题（观察）
3. 修改有问题的地方（行动）
4. 再读一遍……重复直到满意

AI 解决编程任务也是这样：
1. 先看看代码长什么样（思考）
2. 发现需要修改的地方（观察）
3. 修改代码（行动）
4. 运行测试检查结果（观察）
5. 如果测试失败，再修改……重复直到通过

这种"螺旋式上升"的模式在很多领域都能看到：科学实验（假设→实验→分析→新假设）、产品开发（原型→用户反馈→改进→新原型）、甚至学习本身（学→练→错→再学）。

理解了 Agent Loop，你就理解了一种通用的问题解决方法。

下一章，我们将深入流式响应——AI 是怎么"一个字一个字"地回复的。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
