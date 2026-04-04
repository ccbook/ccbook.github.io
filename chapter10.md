# 第10章：流式响应——逐字显示的魔法

## 为什么需要流式？

你有没有注意到，当你问 Claude 一个问题时，回答是一个字一个字出现的，而不是"嘭"一下全部显示？这就是**流式响应（Streaming）**。

为什么要这样？想象两种体验：

**方式A（非流式）**：你问了一个问题。等了 15 秒，屏幕上什么都没有。然后突然出现一大段文字。

**方式B（流式）**：你问了一个问题。0.5 秒后开始出现文字，一个词一个词地"打"出来，15 秒后打完。

两种方式总时间差不多，但方式 B 的体验好得多——因为你能**立刻看到 AI 在工作**，而不是对着空白屏幕焦虑地等待。

这在心理学上叫做**感知延迟**——同样是等 15 秒，有反馈的等待比没有反馈的等待感觉快得多。

## 流式的工作原理

流式响应使用一种叫 **Server-Sent Events (SSE)** 的协议。它的工作方式像这样：

```
客户端发送请求
    ↓
服务器开始生成回复
    ↓
生成了几个字 → 立刻发给客户端
生成了几个字 → 立刻发给客户端
生成了几个字 → 立刻发给客户端
...
生成完毕 → 发送结束信号
```

与普通 HTTP 请求不同（发送请求 → 等待 → 收到完整响应），SSE 保持连接打开，服务器随时可以发送数据。

## 事件的种类

Claude API 在流式模式下会发送以下类型的事件：

```
message_start          开始一条新消息
  │
  ├── content_block_start  开始一个内容块（文字/工具调用/思考）
  │     │
  │     ├── content_block_delta  增量内容（几个字/几个字节的 JSON）
  │     ├── content_block_delta
  │     ├── content_block_delta
  │     │   ...
  │     │
  │     └── content_block_stop   内容块结束
  │
  ├── content_block_start  另一个内容块
  │     │
  │     └── ...
  │
  └── message_stop         消息结束
```

让我们看一个真实的例子。当 AI 回复 "你好，让我看看那个文件。" 时，事件序列是：

```
event: message_start
data: { "type": "message_start", "message": { "id": "msg_123", "role": "assistant" } }

event: content_block_start
data: { "type": "content_block_start", "index": 0, "content_block": { "type": "text", "text": "" } }

event: content_block_delta
data: { "type": "content_block_delta", "delta": { "type": "text_delta", "text": "你好" } }

event: content_block_delta
data: { "type": "content_block_delta", "delta": { "type": "text_delta", "text": "，让我" } }

event: content_block_delta
data: { "type": "content_block_delta", "delta": { "type": "text_delta", "text": "看看那个" } }

event: content_block_delta
data: { "type": "content_block_delta", "delta": { "type": "text_delta", "text": "文件。" } }

event: content_block_stop
data: { "type": "content_block_stop", "index": 0 }

event: message_stop
data: { "type": "message_stop" }
```

每个 `text_delta` 只包含几个字，立刻发送给客户端。客户端把这些字拼接起来，就得到了完整的回复。

## Claude Code 中的流式处理

Claude Code 使用异步生成器来处理流式事件：

```typescript
async function* processStream(stream: AsyncIterable<StreamEvent>) {
  let currentText = ""
  let currentToolUse = null

  for await (const event of stream) {
    switch (event.type) {
      case "content_block_start":
        if (event.content_block.type === "text") {
          currentText = ""
        } else if (event.content_block.type === "tool_use") {
          currentToolUse = {
            id: event.content_block.id,
            name: event.content_block.name,
            inputJson: "",
          }
        }
        break

      case "content_block_delta":
        if (event.delta.type === "text_delta") {
          currentText += event.delta.text
          // 立刻把这几个字显示给用户
          yield { type: "text_update", text: event.delta.text }
        }
        if (event.delta.type === "input_json_delta") {
          currentToolUse.inputJson += event.delta.partial_json
          // 工具的输入参数也在逐步到来
        }
        break

      case "content_block_stop":
        if (currentToolUse) {
          // 工具输入完整了，可以解析 JSON
          const input = JSON.parse(currentToolUse.inputJson)
          yield {
            type: "tool_use_complete",
            tool: currentToolUse.name,
            input: input,
          }
        }
        break

      case "message_stop":
        yield { type: "message_complete" }
        break
    }
  }
}
```

## 界面的实时更新

当流式事件到来时，界面需要实时更新。这就是 React 发挥作用的地方：

```typescript
function StreamingMessage() {
  const [text, setText] = useState("")
  const [isStreaming, setIsStreaming] = useState(true)

  useEffect(() => {
    const processEvents = async () => {
      for await (const event of processStream(stream)) {
        if (event.type === "text_update") {
          setText(prev => prev + event.text)
        }
        if (event.type === "message_complete") {
          setIsStreaming(false)
        }
      }
    }
    processEvents()
  }, [])

  return (
    <Box>
      <Text>{text}</Text>
      {isStreaming && <Spinner />}
    </Box>
  )
}
```

每收到一个 `text_update`，调用 `setText()` 追加新文字。React 检测到状态变化，自动重新渲染组件——用户就看到了新出现的文字。

## 加载动画与 Token 计数

在 AI "思考"（生成回复）的过程中，Claude Code 显示一个加载动画：

```
⠋ Thinking... (1,234 tokens)
```

这个 token 计数是实时更新的。怎么做到的？

```typescript
function ThinkingSpinner() {
  const [tokenCount, setTokenCount] = useState(0)
  const [frame, setFrame] = useState(0)

  // 旋转动画帧
  const spinnerFrames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

  useEffect(() => {
    const timer = setInterval(() => {
      setFrame(f => (f + 1) % spinnerFrames.length)
    }, 80)  // 每 80ms 换一帧
    return () => clearInterval(timer)
  }, [])

  return (
    <Text>
      <Text color="cyan">{spinnerFrames[frame]}</Text>
      {" "}Thinking... ({tokenCount.toLocaleString()} tokens)
    </Text>
  )
}
```

Token 计数的估算方式很简单：

```typescript
// 每收到一些文字，就估算 token 数
const estimatedTokens = Math.ceil(receivedCharacters / 4)
```

大约每 4 个字符是 1 个 token。这只是估算，但对实时显示来说足够准确了。

## 中断：用户按了 Ctrl+C

如果 AI 正在回复，用户突然按了 Ctrl+C 想打断它怎么办？

Claude Code 有三种处理方式：

```typescript
function handleInterrupt(currentState) {
  if (currentState === "streaming_text") {
    // AI 正在说话 → 停止接收，显示已收到的部分
    stream.abort()
    showPartialResponse()
  }

  if (currentState === "executing_tool") {
    // 正在执行工具 → 取决于工具的中断行为
    const behavior = currentTool.interruptBehavior()

    if (behavior === "cancel") {
      // 取消工具执行
      currentTool.cancel()
    } else if (behavior === "block") {
      // 等待工具完成（不能取消，比如正在写文件）
      showMessage("等待当前操作完成...")
    }
  }
}
```

每个工具可以定义自己的"中断行为"：
- `cancel`：可以安全取消（如读文件）
- `block`：不能取消，必须等待完成（如写文件——写到一半中断会导致文件损坏）

## 细粒度工具流式输入

一个有趣的优化：工具的输入参数也可以流式处理。

以 Bash 工具为例。AI 可能要运行一个很长的命令：

```json
{
  "name": "Bash",
  "input": {
    "command": "find /Users/project -name '*.ts' -exec grep -l 'import React' {} \\; | sort | head -20"
  }
}
```

传统方式：等 AI 生成完整个命令字符串后，才开始执行。

流式方式：AI 还在生成命令的时候，Claude Code 就已经知道工具名是 "Bash" 了，可以提前做准备工作（比如检查权限）。

```typescript
// Fine-Grained Tool Streaming (FGTS)
{
  eager_input_streaming: true  // 启用细粒度流式
}
```

当这个特性启用时：
1. AI 开始生成工具输入 → Claude Code 收到工具名
2. 立刻开始权限检查和分类器评估
3. AI 生成完输入 → 权限检查已经完成了
4. 立刻开始执行工具

这个优化可以节省几百毫秒的延迟——对用户来说就是"更快的响应"。

## 思考块：AI 的思考过程

某些模型支持"思考"功能——AI 可以先在内部思考，再给出回答：

```
事件序列：
  content_block_start → { type: "thinking" }
  thinking_delta → "让我分析一下这个问题..."
  thinking_delta → "首先，我需要理解代码结构..."
  thinking_delta → "然后，我发现 bug 在第 42 行..."
  content_block_stop
  content_block_start → { type: "text" }
  text_delta → "我找到了问题。在第 42 行..."
```

思考块让用户能看到 AI 的推理过程，就像看到一个老师在黑板上演算解题步骤。

## 本章小结

- **流式响应**让 AI 的回复实时显示，大幅改善用户体验
- 使用 **SSE 协议**，服务器持续发送小块数据
- 事件类型：message_start → content_block_start → delta → stop
- React 的状态更新机制与流式完美配合
- 加载动画用 Unicode 盲文字符实现"旋转"效果
- **中断处理**根据工具类型决定"取消"还是"等待"
- **细粒度工具流式输入**提前开始权限检查，节省延迟
- **思考块**让用户看到 AI 的推理过程

## 思考题

1. 如果网络很慢，流式响应会有什么体验问题？（提示：文字出现可能会一卡一卡的）
2. 为什么写文件操作不能被中断？如果强制中断会发生什么？
3. "感知延迟"这个概念在日常生活中还有哪些例子？

## 动手实验：体验流式的力量

如果你想亲自体验流式 vs 非流式的差异，试试在 Node.js 中运行这个实验：

```javascript
// experiment.js - 模拟流式和非流式的体验差异

// 非流式：等待 3 秒后一次性显示
async function nonStreaming() {
  console.log("非流式模式：请等待...\n")
  await new Promise(r => setTimeout(r, 3000))
  console.log("Hello! I am Claude, and I can help you with coding tasks.")
}

// 流式：立刻开始逐字显示
async function streaming() {
  console.log("流式模式：\n")
  const text = "Hello! I am Claude, and I can help you with coding tasks."
  for (const char of text) {
    process.stdout.write(char)
    await new Promise(r => setTimeout(r, 50))  // 每个字延迟 50ms
  }
  console.log()
}

// 先体验非流式，再体验流式
nonStreaming().then(() => {
  console.log("\n---\n")
  return streaming()
})
```

运行 `node experiment.js`，你会明显感受到两种方式的体验差异。

下一章，我们将学习上下文管理——AI 如何在有限的"记忆"中做到最好。
