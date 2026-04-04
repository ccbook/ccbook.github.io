# 第3章：从零理解 TypeScript 与 React

## 为什么需要这一章？

Claude Code 是用 TypeScript 写的，界面部分用了 React。如果你只学过 Python 或 C++，可能对这两个技术不太熟悉。别担心——这一章会给你足够的知识来理解后续的源码。

我们不会面面俱到，只讲读源码需要的核心概念。

## TypeScript 速成

### TypeScript 是什么？

TypeScript 是 JavaScript 的"加强版"。它在 JavaScript 的基础上加了一个东西：**类型系统**。

JavaScript 是这样的：

```javascript
let name = "Claude"
let age = 3
let isActive = true
```

TypeScript 是这样的：

```typescript
let name: string = "Claude"
let age: number = 3
let isActive: boolean = true
```

看到区别了吗？TypeScript 在每个变量后面加了 `: 类型`。这告诉编译器（和你的同事）这个变量应该是什么类型。

为什么要这样？因为在一个 50 万行的项目里，如果一个函数期望接收一个数字，你却传了一个字符串，JavaScript 不会提前告诉你——它会在运行时才出错。TypeScript 会在**编写代码时**就告诉你："嘿，这里类型不对！"

### 基本类型

```typescript
// 基础类型
let text: string = "hello"
let num: number = 42
let flag: boolean = true
let nothing: null = null
let notDefined: undefined = undefined

// 数组
let numbers: number[] = [1, 2, 3]
let names: string[] = ["Alice", "Bob"]

// 对象
let person: { name: string; age: number } = {
  name: "Alice",
  age: 16
}
```

### type 和 interface——自定义类型

在 Claude Code 的源码里，你会看到大量的 `type` 和 `interface`。它们的作用是给复杂的数据结构起个名字：

```typescript
// 用 type 定义一个类型
type Message = {
  id: string
  role: "user" | "assistant"  // 只能是这两个值之一
  content: string
  timestamp: number
}

// 用 interface 定义一个接口（功能类似）
interface Tool {
  name: string
  description: string
  call(input: unknown): Promise<ToolResult>
}
```

`type` 和 `interface` 的区别不大，你可以简单理解为"两种定义类型的方式"。Claude Code 主要用 `type`。

### 泛型——类型的"参数"

这是 TypeScript 中稍微高级一点的概念。看这个例子：

```typescript
// 没有泛型：我们需要为每种类型写一个函数
function getFirstNumber(arr: number[]): number { return arr[0] }
function getFirstString(arr: string[]): string { return arr[0] }

// 有泛型：一个函数搞定所有类型
function getFirst<T>(arr: T[]): T { return arr[0] }

// 使用时指定具体类型
getFirst<number>([1, 2, 3])     // 返回 number
getFirst<string>(["a", "b"])    // 返回 string
```

`<T>` 就像一个"类型占位符"。你可以把泛型想象成**类型的变量**——就像普通变量可以存储不同的值，泛型可以代表不同的类型。

在 Claude Code 里，你会经常看到这样的代码：

```typescript
type Tool<Input, Output, Progress> = {
  name: string
  call(args: Input): Promise<ToolResult<Output>>
  onProgress?: (data: Progress) => void
}
```

这意味着"Tool"是一个通用的模板，不同的工具可以有不同的输入类型、输出类型和进度类型。

### async/await——异步编程

Claude Code 里几乎所有重要的函数都是异步的。什么是异步？

想象你在餐厅点餐。同步就是：你站在柜台前等，直到饭做好了才离开。异步就是：你点完餐后回到座位上做别的事，饭好了服务员叫你。

```typescript
// 同步：一行一行执行，每行都要等上一行完成
const content = readFileSync("index.ts")  // 可能要等 100ms
console.log(content)

// 异步：发起操作后继续执行，操作完成后再处理结果
const content = await readFile("index.ts")  // 等待，但不阻塞其他任务
console.log(content)
```

`async` 标记一个函数是异步的，`await` 等待异步操作完成。在 Claude Code 里，读文件、调 API、执行命令都是异步的，因为这些操作需要时间。

### Promise——异步的载体

`Promise` 是 JavaScript 处理异步操作的核心概念。你可以把它想象成一张"承诺书"：

```typescript
// fetchData() 返回一个 Promise
// 这个 Promise"承诺"将来会给你一个 string
function fetchData(): Promise<string> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve("数据来了！")
    }, 1000)
  })
}

// 用 await 等待承诺兑现
const data = await fetchData()  // 1秒后得到 "数据来了！"
```

### import/export——模块系统

大型项目需要把代码分成很多文件。`import` 和 `export` 就是文件之间分享代码的方式：

```typescript
// tools/BashTool.ts —— 导出
export const BashTool = {
  name: "Bash",
  call: async (input) => { /* ... */ }
}

// main.ts —— 导入
import { BashTool } from "./tools/BashTool"
```

你也会看到 `require()`，这是更老的导入方式，但在 Claude Code 里还被用于"延迟加载"：

```typescript
// 只在需要时才加载这个模块（节省启动时间）
const VoiceModule = feature('VOICE_MODE')
  ? require('./voice/index.js')
  : null
```

## React 速成

### React 是什么？

React 是一个用来构建用户界面的框架。它最初是为网页设计的，但 Claude Code 用了一个叫 **Ink** 的库，让 React 可以在终端里画界面。

React 的核心思想是：**用数据描述界面，数据变了界面自动更新。**

### 组件——界面的积木

React 的基本单位是"组件"。组件就像乐高积木——你用小积木拼成大积木：

```typescript
// 一个简单的组件
function Greeting({ name }: { name: string }) {
  return <Text>你好，{name}！</Text>
}

// 使用组件
<Greeting name="同学" />
// 显示：你好，同学！
```

这里的 `<Text>你好，{name}！</Text>` 看起来像 HTML，但其实是 **JSX**——一种在 JavaScript 里写界面的语法。

### 组件的组合

大组件由小组件组成：

```typescript
function App() {
  return (
    <Box flexDirection="column">
      <Header title="Claude Code" />
      <MessageList messages={messages} />
      <InputBox onSubmit={handleSubmit} />
    </Box>
  )
}
```

Claude Code 的整个终端界面就是这样一层层组合起来的。

### useState——组件的记忆

组件需要记住一些数据（比如用户输入了什么）。`useState` 就是给组件添加"记忆"的方式：

```typescript
function Counter() {
  const [count, setCount] = useState(0)
  //     ↑值     ↑修改值的函数    ↑初始值

  return (
    <Box>
      <Text>当前计数：{count}</Text>
      <Button onPress={() => setCount(count + 1)}>
        +1
      </Button>
    </Box>
  )
}
```

当你调用 `setCount(1)` 时，React 会自动重新渲染组件，显示新的值。

### useEffect——副作用

有时候组件需要做一些"额外的事情"，比如发网络请求、设置定时器等。这些叫"副作用"：

```typescript
function Clock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    // 组件"出生"后开始执行
    const timer = setInterval(() => {
      setTime(new Date())
    }, 1000)

    // 组件"消亡"前清理
    return () => clearInterval(timer)
  }, []) // 空数组表示只在组件出生时执行一次

  return <Text>{time.toLocaleTimeString()}</Text>
}
```

### 自定义 Hook——复用逻辑

当你发现多个组件有相似的逻辑时，可以把它提取成"自定义 Hook"：

```typescript
// 自定义 Hook：管理权限检查
function useCanUseTool() {
  const [permissions, setPermissions] = useState({})
  
  async function checkPermission(tool: string, input: any) {
    // 检查权限的逻辑...
    return { allowed: true }
  }

  return { checkPermission, permissions }
}

// 在组件中使用
function ToolExecutor() {
  const { checkPermission } = useCanUseTool()
  // ...
}
```

Claude Code 有 87 个自定义 Hook，每个都封装了一种特定的逻辑。

## Zod——运行时类型检查

Claude Code 使用一个叫 **Zod** 的库来做运行时的数据验证。TypeScript 的类型只在编写代码时检查；而 Zod 在程序**运行时**也能检查数据是否正确。

```typescript
import { z } from "zod"

// 定义一个 schema（数据的"模具"）
const MessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
  timestamp: z.number()
})

// 验证数据
const result = MessageSchema.safeParse({
  role: "user",
  content: "你好",
  timestamp: 1234567890
})

if (result.success) {
  console.log("数据格式正确！", result.data)
} else {
  console.log("数据格式错误！", result.error)
}
```

为什么需要运行时检查？因为 AI 返回的数据可能不符合预期格式，外部 API 的数据也可能有问题。Zod 就是在程序运行时守护数据质量的"门卫"。

在 Claude Code 里，每个工具的输入都用 Zod 来定义和验证：

```typescript
const BashToolInputSchema = z.object({
  command: z.string().describe("要执行的命令"),
  timeout: z.number().optional().describe("超时时间（毫秒）"),
})
```

## Zustand——状态管理

Claude Code 用 **Zustand**（德语中"状态"的意思）来管理全局状态。什么是全局状态？就是整个程序都需要访问的数据，比如：
- 当前的对话消息列表
- 用户的权限设置
- 当前使用的 AI 模型

```typescript
// 创建一个全局状态仓库
const useStore = create((set) => ({
  messages: [],
  addMessage: (msg) => set((state) => ({
    messages: [...state.messages, msg]
  })),
  theme: "dark",
  setTheme: (theme) => set({ theme }),
}))

// 在任何组件中使用
function MessageList() {
  const messages = useStore(state => state.messages)
  return messages.map(msg => <Message key={msg.id} {...msg} />)
}
```

`useStore(state => state.messages)` 的意思是："从全局状态中取出 `messages`，当 `messages` 变化时重新渲染这个组件。"

## Ink——终端里的 React

最后介绍一下 **Ink**，它是让 React 在终端里工作的魔法。

普通的 React 在浏览器里运行，用 HTML 元素（`<div>`、`<span>`、`<button>`）来构建界面。Ink 把这些替换成了终端元素：

| 浏览器 React | 终端 Ink |
|-------------|---------|
| `<div>` | `<Box>` |
| `<span>` | `<Text>` |
| `<input>` | `<TextInput>` |
| CSS flexbox | Box 的 flexDirection 等属性 |

```typescript
// Ink 版的终端界面
import { Box, Text } from "ink"

function App() {
  return (
    <Box flexDirection="column" padding={1}>
      <Box borderStyle="round" borderColor="cyan">
        <Text bold color="cyan">Claude Code</Text>
      </Box>
      <Text>请输入你的问题：</Text>
      <TextInput onSubmit={handleSubmit} />
    </Box>
  )
}
```

这段代码会在终端里画出一个带边框的标题和一个输入框。是不是很神奇？

## 你会在源码中遇到的常见模式

### 模式一：条件导出

```typescript
// 根据功能开关决定是否包含某个工具
export function getAllBaseTools(): Tools {
  return [
    BashTool,
    FileReadTool,
    ...(isFeatureEnabled('VOICE') ? [VoiceTool] : []),
  ]
}
```

`...()` 是展开运算符，`? :` 是三元表达式。合在一起就是："如果 VOICE 功能开启，就把 VoiceTool 加进数组，否则不加。"

### 模式二：异步生成器

```typescript
async function* streamResponse(): AsyncGenerator<StreamEvent> {
  for await (const chunk of apiStream) {
    yield processChunk(chunk)
  }
}
```

`function*` 定义一个"生成器"函数，`yield` 每次"吐出"一个值。配合 `async`，就可以逐块处理流式数据。Claude Code 用这个模式来实现逐字显示 AI 回复。

### 模式三：选择器模式

```typescript
const verbose = useAppState(s => s.verbose)
```

`s => s.verbose` 是一个"选择器"——从大的状态对象中选出你关心的那部分。这样当 `verbose` 没变时，组件不会多余地重新渲染。

## 本章小结

- **TypeScript** = JavaScript + 类型系统，帮助在大型项目中减少错误
- **React** 用组件构建界面，数据变化时界面自动更新
- **Zod** 在运行时验证数据格式
- **Zustand** 管理全局共享状态
- **Ink** 让 React 能在终端里画界面
- 常见模式：条件导出、异步生成器、选择器

## 快速参考卡片

以下是你在阅读后续章节时最常遇到的语法，可以随时翻回来查看：

```
TypeScript 速查
━━━━━━━━━━━━━━
let x: string = "hi"        变量声明 + 类型
type Foo = { a: number }     自定义类型
<T>(x: T) => T               泛型函数
async/await                   异步操作
import/export                 模块导入导出
?.                            可选链（a?.b 等于 a 存在则 a.b）
??                            空值合并（a ?? b 等于 a 为空则用 b）
...arr                        展开运算符
`模板${变量}字符串`            模板字符串

React/Ink 速查
━━━━━━━━━━━━━━
<Component prop={value} />   使用组件
useState(初始值)              状态 Hook
useEffect(() => {}, [])      副作用 Hook
{condition && <X />}          条件渲染
{arr.map(x => <X key={x} />)} 列表渲染
```

有了这些基础知识，你就准备好深入 Claude Code 的源码了。下一章，我们将打开程序的大门——`main.tsx`。
