# 第22章：IDE 桥接——编辑器中的 AI

## 两个世界的融合

程序员通常在两个地方工作：

1. **IDE（集成开发环境）**：VS Code、JetBrains 等——写代码、看文件、调试
2. **终端（Terminal）**：运行命令、管理 Git、执行脚本

Claude Code 最初只能在终端里使用。但程序员在写代码时更多时间待在 IDE 里，如果每次都要切换到终端去和 AI 对话，很不方便。

**桥接系统（Bridge）**就是为了解决这个问题——它让 Claude Code 可以在 IDE 里直接使用。

## 桥接的架构

```
┌─────────────────────────────────────────────┐
│                 IDE (VS Code)                │
│                                              │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │ 代码编辑器    │    │ Claude Code 面板  │   │
│  │              │    │                   │   │
│  │  你的代码    │    │  与 AI 的对话     │   │
│  │  在这里      │    │  在这里           │   │
│  │              │    │                   │   │
│  └──────────────┘    └─────────┬─────────┘   │
│                                │              │
└────────────────────────────────┼──────────────┘
                                 │
                     WebSocket / HTTP
                                 │
                    ┌────────────┴────────────┐
                    │  Claude Code 进程        │
                    │  (--bridge 模式)         │
                    │                          │
                    │  查询引擎                │
                    │  工具执行                │
                    │  权限管理                │
                    └──────────────────────────┘
```

IDE 扩展是"前端"，Claude Code 进程是"后端"。它们之间通过 WebSocket 或 HTTP 通信。

## 桥接的启动流程

```
1. 用户在 VS Code 中打开 Claude Code 面板
    │
    ▼
2. IDE 扩展启动一个 Claude Code 子进程
   claude --bridge --session-id=abc123
    │
    ▼
3. 子进程进入桥接模式
   - 不启动终端 UI
   - 改为监听 WebSocket 连接
    │
    ▼
4. IDE 扩展通过 WebSocket 连接到子进程
    │
    ▼
5. 双向通信建立
   IDE → Claude Code: 用户消息、选中的代码、文件上下文
   Claude Code → IDE: AI 回复、文件修改、工具执行状态
```

## JWT 认证

桥接通信需要安全认证——你不希望其他程序冒充 IDE 来控制 Claude Code。

Claude Code 使用 **JWT（JSON Web Token）**来认证：

```
IDE 扩展持有一个密钥
  ↓
用密钥签名一个 JWT
  ↓
每次请求都带上 JWT
  ↓
Claude Code 验证 JWT
  ↓
验证通过才处理请求
```

JWT 就像一个"门禁卡"——只有持有正确门禁卡的人才能进门。

## IDE 与 Claude Code 的交互

### 发送当前文件上下文

当你在 IDE 中打开了一个文件并和 AI 对话时，IDE 会自动把文件信息发送给 Claude Code：

```typescript
// IDE 扩展发送的上下文
{
  type: "context",
  activeFile: {
    path: "/Users/alice/project/src/app.ts",
    content: "...",
    language: "typescript",
    selection: {  // 用户选中的文本
      start: { line: 10, character: 0 },
      end: { line: 15, character: 20 },
      text: "const result = fetchData()"
    }
  },
  openFiles: [
    "src/app.ts",
    "src/utils.ts",
    "package.json"
  ],
  diagnostics: [  // 编辑器检测到的问题
    { line: 12, message: "Type 'string' is not assignable to type 'number'" }
  ]
}
```

这样 AI 就知道你正在看哪个文件、选中了哪段代码、有什么错误。

### 在 IDE 中显示差异

当 AI 修改了文件，修改会发送回 IDE，在编辑器里显示差异对比：

```typescript
// Claude Code 发送给 IDE 的修改
{
  type: "fileEdit",
  path: "/Users/alice/project/src/app.ts",
  changes: [
    {
      range: { start: { line: 10 }, end: { line: 10 } },
      oldText: "const result = fetchData()",
      newText: "const result = await fetchData()"
    }
  ]
}
```

IDE 收到后，会在编辑器里高亮显示修改——你可以直接接受或拒绝每个修改。

### 导航到代码位置

AI 可以告诉 IDE "跳转到某个位置"：

```typescript
{
  type: "navigate",
  path: "src/utils.ts",
  line: 42,
  character: 10
}
```

IDE 收到后，会自动打开文件并跳到指定位置。

## 多会话支持

一个 IDE 窗口可以同时运行多个 Claude Code 会话：

```
VS Code
├── 会话 1: 正在帮你修复 bug（src/app.ts）
├── 会话 2: 正在帮你写测试（test/app.test.ts）
└── 会话 3: 正在帮你审查 PR #123
```

每个会话是一个独立的 Claude Code 进程，有自己的上下文和对话历史。

## 桥接的好处

### 1. 无缝集成

不需要在 IDE 和终端之间切换。代码和 AI 对话在同一个窗口里。

### 2. 丰富的上下文

IDE 可以提供比终端更丰富的上下文：当前文件、选中文本、编辑器诊断、打开的文件列表等。

### 3. 直观的代码修改

在 IDE 里直接看到差异对比，可以逐行接受或拒绝。比终端里的文本差异更直观。

### 4. 代码导航

AI 可以直接控制 IDE 打开文件、跳转到特定行。在终端里这是做不到的。

## 本章小结

- 桥接系统让 Claude Code 在 IDE 中运行
- 架构：IDE 扩展（前端）← WebSocket → Claude Code 进程（后端）
- JWT 认证确保通信安全
- IDE 提供丰富上下文：当前文件、选中文本、诊断信息
- 支持在 IDE 中直接显示差异对比、代码导航
- 支持多会话并行

## 前后端分离的经典模式

IDE 桥接系统是**前后端分离**模式的经典案例。

```
传统方式（一体化）：
  [所有功能集中在一个程序里]
  → 改界面需要重新部署整个程序
  → 不能有多种界面

前后端分离：
  [前端: IDE 扩展]  ←→  [后端: Claude Code]
  → 换一个前端（从 VS Code 换到 JetBrains）不影响后端
  → 可以同时有终端界面、IDE 界面、Web 界面
  → 每个部分可以独立开发和更新
```

你可能在 Web 开发中也会遇到这种模式：
- **前端**：网页界面（React, Vue 等）
- **后端**：服务器逻辑（Node.js, Python 等）
- **通信**：HTTP API / WebSocket

Claude Code 的桥接系统和 Web 开发的前后端分离本质上是同一种架构模式——只不过"前端"从浏览器变成了 IDE 扩展。

下一章，我们将了解插件和技能系统——让 Claude Code 无限扩展。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
