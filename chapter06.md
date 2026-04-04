# 第6章：状态管理——程序的"记忆"

## 什么是"状态"？

想象你正在玩一个游戏。游戏需要记住很多东西：你的生命值、你在地图上的位置、你拥有的道具、当前的关卡……这些需要被记住的东西，就是"状态"。

Claude Code 也需要记住很多东西：

- 当前对话的所有消息
- 用户选择的 AI 模型
- 权限设置
- 当前正在执行的工具
- 主题颜色
- 后台任务的进度
- ……

这些信息需要在程序的各个部分之间共享。比如，当 AI 发来一条新消息时，消息列表组件需要知道，状态栏的 token 计数也需要更新。

## 为什么需要状态管理？

在一个小程序里，你可以用简单的变量来存储状态：

```typescript
let messages = []
let currentModel = "claude-sonnet"

function addMessage(msg) {
  messages.push(msg)
  updateUI()  // 手动更新界面
}
```

但在一个有 146 个组件的大程序里，这种方式会变成灾难：

1. **谁来调用 `updateUI()`？** 任何改变状态的代码都得记得更新界面
2. **更新哪些部分？** 不是所有组件都关心所有状态
3. **状态冲突？** 两段代码同时修改同一个状态怎么办？
4. **调试困难？** 状态在哪里被修改的？很难追踪

这就是为什么需要专门的"状态管理"方案。

## Zustand：Claude Code 的状态管理

Claude Code 使用 **Zustand** 来管理全局状态。Zustand 是一个非常轻量的状态管理库（核心代码不到 100 行），但功能强大。

### 创建状态仓库

```typescript
import { create } from "zustand"

// 定义状态的形状
type AppState = {
  // 会话相关
  sessionId: string
  conversationId: string
  messages: Message[]

  // 模型相关
  mainLoopModel: string

  // UI 相关
  theme: string
  verbose: boolean

  // 权限相关
  toolPermissionContext: ToolPermissionContext

  // 任务相关
  backgroundTasks: Map<string, TaskState>

  // 方法（修改状态的函数）
  addMessage: (msg: Message) => void
  setTheme: (theme: string) => void
  setModel: (model: string) => void
}

// 创建仓库
const useAppState = create<AppState>((set) => ({
  sessionId: generateUUID(),
  conversationId: generateUUID(),
  messages: [],
  mainLoopModel: "claude-sonnet",
  theme: "dark",
  verbose: false,
  toolPermissionContext: defaultPermissions,
  backgroundTasks: new Map(),

  addMessage: (msg) => set((state) => ({
    messages: [...state.messages, msg]
  })),

  setTheme: (theme) => set({ theme }),

  setModel: (model) => set({ mainLoopModel: model }),
}))
```

### 在组件中使用状态

```typescript
// 方式一：获取单个值
function StatusBar() {
  const model = useAppState(s => s.mainLoopModel)
  const theme = useAppState(s => s.theme)

  return (
    <Box>
      <Text>模型: {model}</Text>
      <Text>主题: {theme}</Text>
    </Box>
  )
}

// 方式二：获取方法
function MessageInput() {
  const addMessage = useAppState(s => s.addMessage)

  function handleSubmit(text: string) {
    addMessage({
      id: generateUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    })
  }

  return <TextInput onSubmit={handleSubmit} />
}
```

### 选择器：精确订阅

`useAppState(s => s.mainLoopModel)` 中的 `s => s.mainLoopModel` 叫做**选择器（Selector）**。

它的作用是什么？告诉 Zustand："我只关心 `mainLoopModel` 这个值，只有当它变化时才通知我重新渲染。"

这很重要！假设我们不用选择器：

```typescript
// 不好的做法：订阅整个状态
function StatusBar() {
  const state = useAppState()  // 获取全部状态

  return <Text>模型: {state.mainLoopModel}</Text>
}
```

这样的话，每当**任何**状态变化（比如新消息到来），StatusBar 都会重新渲染，即使它只显示模型名称。在一个频繁更新的应用里，这会导致严重的性能问题。

用选择器就像订阅报纸：你只订阅"体育版"，就不会收到"财经版"的更新通知。

## Claude Code 的状态结构

让我们看看 Claude Code 实际的状态结构：

```
AppState
├── 会话信息
│   ├── sessionId          — 本次会话的唯一标识
│   ├── conversationId     — 对话的唯一标识
│   └── messages[]         — 所有消息的列表
│
├── 模型配置
│   ├── mainLoopModel      — 当前使用的 AI 模型
│   └── lastTokenCount     — 上次使用的 token 数量
│
├── UI 状态
│   ├── theme              — 当前主题
│   ├── verbose            — 是否显示详细信息
│   ├── spinner            — 加载动画的状态
│   └── notifications[]    — 通知消息队列
│
├── 权限
│   └── toolPermissionContext — 完整的权限配置
│       ├── mode           — 权限模式（default/auto/bypass）
│       ├── alwaysAllowRules — 总是允许的规则
│       ├── alwaysDenyRules  — 总是拒绝的规则
│       └── alwaysAskRules   — 总是询问的规则
│
├── 工具与功能
│   ├── selectedTools[]    — 当前可用的工具列表
│   ├── toolSearchResults  — 工具搜索的结果
│   └── skillSuggestions[] — 技能建议
│
├── 任务
│   ├── backgroundTasks    — 后台运行的任务
│   └── focusedTaskId      — 当前聚焦的任务
│
├── 智能体
│   └── activeSubagents    — 活跃的子智能体
│
├── 记忆
│   ├── claudeMdPath       — CLAUDE.md 文件的路径
│   └── nestedMemoryAttachments — 嵌套的记忆附件
│
├── 权限队列
│   └── toolPermissionQueue — 等待用户确认的权限请求
│
└── 性能追踪
    └── costTracker        — 费用追踪器
```

这是一个相当大的状态树。但因为使用了选择器模式，每个组件只关心它需要的那一小部分。

## 状态的生命周期

让我们跟踪一个状态变化的完整过程：

```
用户输入 "帮我读取 index.ts"
    │
    ▼
1. 创建用户消息对象
   { role: "user", content: "帮我读取 index.ts" }
    │
    ▼
2. 调用 addMessage()
   → Zustand 更新 state.messages
    │
    ▼
3. 订阅了 messages 的组件收到通知
   → MessageList 重新渲染，显示新消息
   → StatusBar 的消息计数更新
    │
    ▼
4. 消息发送给 Claude API
    │
    ▼
5. AI 回复到来，创建 assistant 消息
   → 再次调用 addMessage()
   → UI 再次更新
    │
    ▼
6. AI 决定使用 FileReadTool
   → toolPermissionQueue 增加一项
   → PermissionRequest 组件显示
    │
    ▼
7. 用户允许
   → 工具执行
   → 结果作为新消息添加
   → UI 更新
```

注意每一步都是通过 Zustand 来协调的。组件不需要直接互相通信——它们都通过"状态仓库"来交换信息。这就像一个公告板：发布者把消息贴上去，关心的人自己来看。

## 不可变更新

在 Zustand（和 React）中，状态更新必须是"不可变的"。什么意思？

```typescript
// ❌ 错误：直接修改状态（可变更新）
addMessage: (msg) => {
  state.messages.push(msg)  // 直接修改了原数组
}

// ✅ 正确：创建新的状态（不可变更新）
addMessage: (msg) => set((state) => ({
  messages: [...state.messages, msg]  // 创建了一个新数组
}))
```

`[...state.messages, msg]` 的意思是：创建一个新数组，把旧数组的所有元素放进去，再加上新消息。

为什么要这样？因为 React 判断"状态有没有变化"时，用的是**引用比较**——它检查新旧状态是不是同一个对象。如果你直接修改原对象，引用没变，React 就不知道要更新界面。

打个比方：这就像你交作业。如果你在原来的纸上改了几个字，老师看一眼"还是那张纸"可能不会注意到你改了。但如果你交一张新纸，老师一定会看到。

## 持久化

有些状态需要在程序关闭后保留下来（比如用户的主题偏好），有些不需要（比如当前的对话消息——那由会话记录系统管理）。

Zustand 支持中间件来实现持久化：

```typescript
// 概念示例
const useSettings = create(
  persist(
    (set) => ({
      theme: "dark",
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "claude-settings",     // 存储的键名
      storage: createJSONStorage(),  // 存储引擎
    }
  )
)
```

但 Claude Code 实际上使用了更复杂的持久化方案——通过 `settings.json` 文件和会话存储系统。这些我们会在后面的章节详细介绍。

## 状态管理的设计智慧

从 Claude Code 的状态管理中，我们可以学到几个设计智慧：

### 1. 单一数据源

所有组件从同一个地方读取状态。这避免了"A 组件认为用户选了模型 X，B 组件认为用户选了模型 Y"的不一致问题。

### 2. 最小订阅原则

每个组件只订阅它需要的状态。这保证了性能——不相关的变化不会导致不必要的重渲染。

### 3. 状态与 UI 分离

状态的定义和管理在 `state/` 目录，UI 的渲染在 `components/` 目录。这意味着你可以换掉整个 UI 框架（比如从 Ink 换成 Web），状态管理的代码一行都不用改。

### 4. 可预测的更新

所有状态变化都通过 `set()` 函数，不会有"不知道谁改了我的状态"的情况。这让调试变得容易得多。

## 本章小结

- **状态**是程序需要记住的数据（消息、设置、权限等）
- **Zustand** 是 Claude Code 使用的状态管理库，轻量但强大
- **选择器**让组件只订阅关心的状态，避免不必要的重渲染
- 状态更新必须是**不可变的**——创建新对象而不是修改旧对象
- 设计智慧：单一数据源、最小订阅、状态与 UI 分离、可预测更新

## 思考题

1. 如果两个组件需要共享一个状态值，你觉得应该怎么办？（提示：把它放在哪里？）
2. 为什么不把所有状态都放在一个组件里，通过属性一层层传下去？（提示：想想 10 层嵌套的情况）
3. 如果一个状态只有一个组件用到，还需要放在全局状态里吗？

## 真实世界的状态管理

状态管理不是编程特有的概念——它无处不在：

**学校的成绩系统**就是一种状态管理：
- 状态：每个学生的各科成绩
- 更新：老师录入新成绩
- 订阅：学生查看自己的成绩，家长收到通知
- 一致性：不能出现"数学老师看到的成绩和班主任看到的不一样"

**微信群聊**也是：
- 状态：聊天记录
- 更新：有人发了新消息
- 订阅：所有群成员都能看到新消息
- 一致性：所有人看到的消息顺序相同

Claude Code 的 Zustand 仓库就像一个"微信群"——所有组件都在这个"群"里。当状态发生变化（有人"发了消息"），所有订阅了这个变化的组件都会收到通知（看到新消息）。

下一章，我们将学习 Claude Code 的命令系统——那些以 `/` 开头的神奇命令。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
