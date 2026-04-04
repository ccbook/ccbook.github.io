# 第25章：性能优化——毫秒必争

## 为什么性能很重要？

对于一个 CLI 工具来说，速度就是用户体验。如果输入 `claude` 后要等 3 秒才出现界面，用户会觉得这个工具"很慢"。如果 AI 每次回复都要等 30 秒，用户会失去耐心。

Claude Code 的工程师们在每个环节都追求更快的速度。让我们看看他们用了哪些技巧。

## 优化一：并行预加载

还记得第 4 章介绍的启动过程吗？

```typescript
// 在导入模块之前就开始耗时操作
startMdmRawRead()        // 读取系统策略 ~20ms
startKeychainPrefetch()  // 读取密钥 ~60ms

// 然后才开始导入模块
import { App } from "./components/App"     // ~100ms
import { createStore } from "./state"       // ~30ms
```

这两个操作和模块导入是**完全独立**的——它们之间没有依赖。所以可以同时进行：

```
不优化时（串行）:
  密钥读取(60ms) → 策略读取(20ms) → 模块导入(130ms) = 210ms

优化后（并行）:
  密钥读取(60ms) ──────────┐
  策略读取(20ms) ───┐      │
  模块导入(130ms)──────────┘ = 130ms
```

节省了 80ms——几乎减少了 40% 的启动时间。

这个优化的关键洞察是：**不要等到需要结果的时候才开始工作，而是尽早开始。**

## 优化二：提示缓存

这是最重要的优化之一，节省了约 **90% 的 token 费用**。

每次 API 请求都包含系统提示词（约 5,000 tokens）和工具定义（约 8,000 tokens）。这 13,000 tokens 每次都一样，但每次都要付费。

通过提示缓存：

```
第一次请求：
  系统提示词(5,000 tokens) → 创建缓存 → 费用 = 5,000 × 正常价格

后续请求：
  系统提示词 → 命中缓存 → 费用 = 5,000 × 0.1 × 正常价格 (90% 折扣)
```

### 为什么工具按名字排序？

```typescript
// 排序前：每次工具顺序可能不同
tools: [FileRead, Bash, Grep, ...]     // 请求 A
tools: [Bash, FileRead, Grep, ...]     // 请求 B → 缓存失效！

// 排序后：顺序始终一致
tools: [Bash, FileRead, Grep, ...]     // 请求 A
tools: [Bash, FileRead, Grep, ...]     // 请求 B → 缓存命中！
```

如果工具顺序变了，系统提示词的文本就变了，缓存就失效了。按名字排序确保每次顺序一致。

这种"为了缓存而保持稳定性"的思维在性能优化中非常常见。

## 优化三：惰性精确计算

Token 计数是一个频繁的操作。精确计算需要 API 调用（~100ms），但估算几乎不花时间：

```typescript
function getTokenCount(text: string): number {
  const estimated = Math.ceil(text.length / 4)

  // 离上限还远？用估算
  if (estimated < MAX_TOKENS * 0.7) {
    return estimated
  }

  // 接近上限？精确计算
  return await exactTokenCount(text)
}
```

**90% 的时间用估算（0ms），10% 的关键时刻才精确计算（100ms）。**

这个策略的名字叫**惰性计算（Lazy Evaluation）**——只有在真正需要精确值的时候才做精确计算。

## 优化四：LRU 文件缓存

当 AI 在同一次对话中多次读取同一个文件时，不需要每次都从磁盘读：

```typescript
const fileCache = new LRU<string, FileContent>(100)  // 最多缓存 100 个文件

async function readFile(path: string): Promise<FileContent> {
  // 缓存命中？直接返回
  const cached = fileCache.get(path)
  if (cached) return cached

  // 缓存未命中？从磁盘读取
  const content = await fs.readFile(path, "utf-8")
  fileCache.set(path, content)
  return content
}
```

**LRU**（Least Recently Used，最近最少使用）是一种缓存淘汰策略——当缓存满了，淘汰最久没用过的条目。

```
缓存(容量3): [C, B, A]  ← A 最久没用

读取 D → 缓存满了 → 淘汰 A
缓存: [D, C, B]

读取 B → B 已在缓存中 → 移到最前
缓存: [B, D, C]
```

## 优化五：推测性执行

当 AI 的回复还在流式传输时，Claude Code 已经可以开始准备：

```
时间线（不优化）:
  AI 流式输出(3s) → 识别工具名 → 权限检查(200ms) → 执行工具(500ms)
  总计: 3.7s

时间线（推测性执行）:
  AI 流式输出(3s) ─────────────────────┐
  AI 输出工具名后立刻开始权限检查(200ms)─┘
  → 执行工具(500ms)
  总计: 3.5s
```

当 AI 刚开始输出工具名（比如 "Bash"）时，Claude Code 就开始权限检查了——不等 AI 输出完整的工具参数。这样权限检查和 AI 生成参数可以并行进行。

## 优化六：延迟加载

不是所有代码都在启动时需要：

```typescript
// 不优化：启动时加载所有模块
import { VoiceModule } from "./voice"         // +50ms
import { BrowserModule } from "./browser"     // +30ms
import { REPLModule } from "./repl"           // +20ms

// 优化：只在需要时才加载
const VoiceModule = feature('VOICE_MODE')
  ? require('./voice')   // 只有开启语音功能才加载
  : null

const BrowserModule = feature('WEB_BROWSER')
  ? require('./browser') // 只有开启浏览器功能才加载
  : null
```

如果 90% 的用户不用语音功能，那 50ms 的加载时间就是浪费。延迟加载确保只加载用户实际需要的模块。

## 优化七：结果截断

工具返回的结果可能非常大。不加限制会导致两个问题：
1. **token 浪费**：大结果占用 AI 的上下文窗口
2. **网络延迟**：大数据传输需要更多时间

```typescript
const MAX_RESULT_CHARS = 500_000  // 50 万字符上限

if (result.length > MAX_RESULT_CHARS) {
  // 截断并保存完整版本到磁盘
  const previewSize = 1000
  return {
    preview: result.slice(0, previewSize),
    fullPath: saveToDisk(result),
    message: `结果太大(${result.length}字符)，已保存到文件`
  }
}
```

## 优化八：性能剖析

你不能优化你不能测量的东西。Claude Code 有内置的性能测量：

```typescript
profileCheckpoint('main_entry')
// ... 导入模块 ...
profileCheckpoint('imports_done')
// ... 初始化 ...
profileCheckpoint('init_done')
// ... 渲染 ...
profileCheckpoint('render_done')

// 输出: main_entry → imports(45ms) → init(30ms) → render(25ms) = 100ms
```

每个 checkpoint 记录当前时间，最后计算每个阶段的耗时。如果某个阶段突然变慢了，工程师能立刻定位到问题。

## 性能优化的哲学

从这些优化中，我们可以总结出几条通用的性能优化原则：

### 1. 并行一切可以并行的

如果两个操作互不依赖，就同时执行它们。

### 2. 缓存重复的计算

如果一个计算的输入没变，就重用上次的结果。

### 3. 延迟不必要的工作

如果现在不需要，就不要做。等需要的时候再做。

### 4. 估算 > 精确（在大多数情况下）

如果估算值已经足够做决定，就不需要精确计算。

### 5. 保持稳定性以利用缓存

排序、规范化等看似多余的步骤，可能是为了保持缓存的有效性。

### 6. 测量，不要猜测

用数据说话。不要凭感觉优化——先测量，找到真正的瓶颈，再优化。

## 本章小结

- **并行预加载**：启动时提前发起耗时操作
- **提示缓存**：节省 90% 的重复 token 费用
- **惰性精确计算**：90% 用估算，10% 精确计算
- **LRU 缓存**：避免重复读取同一文件
- **推测性执行**：提前开始后续步骤
- **延迟加载**：只加载需要的模块
- **结果截断**：避免大数据占用资源
- **性能剖析**：用数据驱动优化决策

## 性能优化的"80/20 法则"

在性能优化中，有一个著名的经验法则：**80% 的性能问题来自 20% 的代码。**

这意味着你不需要优化每一行代码——你只需要找到那 20% 的"热点代码"，优化它们就能获得 80% 的性能提升。

Claude Code 的优化策略完美体现了这一点：

```
优化投入 vs 收益：

提示缓存：
  投入：修改 API 调用方式（~100 行代码）
  收益：节省 90% token 费用
  → 高收益，值得做

工具排序：
  投入：加一行排序代码
  收益：保持缓存命中率
  → 极低投入，高收益

并行预加载：
  投入：调整代码顺序（~20 行）
  收益：启动快 65ms
  → 低投入，可观收益
```

相反，花一周时间优化一个只被调用一次的函数，即使性能提升 100 倍，对用户体验也没有感知——这就是"过度优化"。

**记住：先测量，再优化。优化有回报的地方，忽略没回报的地方。**

下一章，我们将探索 Claude Code 的记忆系统——跨越会话的智慧。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
