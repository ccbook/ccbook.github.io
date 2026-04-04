# 第20章：MCP 协议——工具的万能接口

## 如果只有内置工具……

Claude Code 内置了 40 多个工具：读文件、搜索代码、执行命令……但世界上有无数的工具和服务：

- 你想让 AI 查询数据库
- 你想让 AI 发送 Slack 消息
- 你想让 AI 操作 Kubernetes 集群
- 你想让 AI 调用你公司内部的 API

不可能把所有这些都内置到 Claude Code 里。那怎么办？

答案是 **MCP（Model Context Protocol，模型上下文协议）**——一个让 Claude Code 连接任何外部工具的标准协议。

## MCP 是什么？

你可以把 MCP 想象成一个"万能插头"：

```
Claude Code ←→ MCP 协议 ←→ 任何工具/服务

就像：
你的手机 ←→ USB-C 接口 ←→ 任何 USB-C 设备
```

不管外部工具是什么（数据库、消息系统、云服务），只要它实现了 MCP 协议，Claude Code 就能使用它。

## MCP 的架构

```
┌─────────────┐     MCP 协议      ┌─────────────────┐
│  Claude Code │ ←──────────────→ │  MCP 服务器 A     │
│  (客户端)    │                   │  (数据库查询)     │
│              │     MCP 协议      ├─────────────────┤
│              │ ←──────────────→ │  MCP 服务器 B     │
│              │                   │  (Slack 消息)     │
│              │     MCP 协议      ├─────────────────┤
│              │ ←──────────────→ │  MCP 服务器 C     │
│              │                   │  (GitHub API)     │
└─────────────┘                   └─────────────────┘
```

- **Claude Code** 是 MCP **客户端**——它知道怎么发送 MCP 请求
- **外部工具** 是 MCP **服务器**——它们知道怎么响应 MCP 请求
- 它们之间通过 MCP 协议通信

## MCP 通信方式

MCP 支持三种通信方式：

### 1. Stdio（标准输入/输出）

```
Claude Code 启动一个子进程
  → 通过 stdin 发送请求
  → 从 stdout 读取响应
```

这是最常用的方式。MCP 服务器就是一个普通的程序，Claude Code 在后台运行它。

### 2. SSE（Server-Sent Events）

```
Claude Code 连接到一个 HTTP 服务器
  → 通过 HTTP POST 发送请求
  → 通过 SSE 流接收响应
```

适合远程服务器。

### 3. WebSocket

```
Claude Code 建立 WebSocket 连接
  → 双向实时通信
```

适合需要实时交互的场景。

## 配置 MCP 服务器

在 Claude Code 的配置文件中添加 MCP 服务器：

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["~/.mcp/github/index.js"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxx"
      }
    },
    "database": {
      "command": "python",
      "args": ["~/.mcp/db-server/main.py"],
      "env": {
        "DATABASE_URL": "postgres://localhost/mydb"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-slack"],
      "env": {
        "SLACK_TOKEN": "xoxb-xxxxxxxxxxxx"
      }
    }
  }
}
```

每个 MCP 服务器的配置包括：
- `command`：启动命令
- `args`：命令参数
- `env`：环境变量（通常包含 API 密钥）

## MCP 工具的发现

当 Claude Code 启动时，它会连接所有配置的 MCP 服务器，并**发现**它们提供的工具：

```typescript
// Claude Code 向 MCP 服务器发送请求
client.request("tools/list")

// MCP 服务器返回工具列表
{
  "tools": [
    {
      "name": "query_database",
      "description": "执行 SQL 查询",
      "inputSchema": {
        "type": "object",
        "properties": {
          "sql": { "type": "string", "description": "SQL 查询语句" }
        }
      }
    },
    {
      "name": "create_table",
      "description": "创建新的数据库表",
      "inputSchema": { ... }
    }
  ]
}
```

这些工具会被自动添加到 AI 的可用工具列表中。

## MCP 工具的命名

MCP 工具在 Claude Code 内部使用特殊的命名格式：

```
mcp__服务器名__工具名
```

例如：

```
mcp__github__create_issue          GitHub 创建 Issue
mcp__database__query_database      数据库查询
mcp__slack__send_message           Slack 发消息
```

这种前缀防止了名字冲突——如果两个 MCP 服务器都有一个叫 `search` 的工具，它们会变成 `mcp__serverA__search` 和 `mcp__serverB__search`。

## MCP 的实际使用

当 AI 需要使用 MCP 工具时，流程和内置工具完全一样：

```
1. AI 决定使用工具
   { "name": "mcp__database__query_database",
     "input": { "sql": "SELECT * FROM users WHERE active = true" } }

2. Claude Code 收到请求
   → 识别出这是 MCP 工具（前缀 "mcp__"）
   → 找到对应的 MCP 服务器（"database"）

3. 转发给 MCP 服务器
   client.request("tools/call", {
     name: "query_database",
     arguments: { sql: "SELECT * FROM users WHERE active = true" }
   })

4. MCP 服务器执行查询
   → 连接数据库
   → 执行 SQL
   → 返回结果

5. 结果返回给 AI
   { "content": [{ "text": "找到 42 个活跃用户..." }] }

6. AI 根据结果继续回复
```

## MCP 的权限控制

MCP 工具同样受权限系统管控：

```json
{
  "permissions": {
    "alwaysAllow": [
      "mcp__github__list_issues",
      "mcp__github__get_issue"
    ],
    "alwaysDeny": [
      "mcp__database__drop_table"
    ],
    "alwaysAsk": [
      "mcp__slack__send_message"
    ]
  }
}
```

你也可以用通配符一次性管理整个服务器的工具：

```json
{
  "alwaysDeny": ["mcp__dangerous_server__*"]
}
```

## MCP 的意义

MCP 的设计非常聪明，它解决了几个关键问题：

### 1. 无限扩展性

任何人都可以写一个 MCP 服务器，提供任何功能。Claude Code 不需要为每种服务都写适配代码。

### 2. 语言无关

MCP 服务器可以用任何编程语言写——Python、JavaScript、Go、Rust……只要遵循 MCP 协议就行。

### 3. 安全隔离

MCP 服务器在独立的进程中运行。即使它崩溃了，也不会影响 Claude Code 本身。

### 4. 标准化

所有 MCP 工具都有统一的接口（JSON Schema 定义输入输出），AI 不需要学习每种工具的特殊用法。

## 本章小结

- **MCP** 是让 Claude Code 连接外部工具的标准协议
- 支持三种通信方式：Stdio、SSE、WebSocket
- 工具通过配置文件注册，启动时自动发现
- MCP 工具命名格式：`mcp__服务器名__工具名`
- 权限系统同样适用于 MCP 工具
- MCP 实现了无限扩展、语言无关、安全隔离和标准化

## 思考题

1. 如果你要为你学校的图书馆系统写一个 MCP 服务器，它应该提供哪些工具？
2. MCP 的三种通信方式各适合什么场景？
3. 为什么 MCP 服务器在独立进程中运行很重要？

## 动手实验：写一个简单的 MCP 服务器

如果你想亲手体验 MCP，可以试试写一个最简单的 MCP 服务器。只需要一个 Node.js 文件：

```javascript
// simple-mcp-server.js
// 一个返回当前时间的 MCP 服务器

const readline = require('readline')

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
})

rl.on('line', (line) => {
  const request = JSON.parse(line)

  if (request.method === 'tools/list') {
    // 告诉客户端我们有哪些工具
    const response = {
      id: request.id,
      result: {
        tools: [{
          name: 'get_time',
          description: '获取当前时间',
          inputSchema: { type: 'object', properties: {} }
        }]
      }
    }
    console.log(JSON.stringify(response))
  }

  if (request.method === 'tools/call') {
    // 执行工具
    const response = {
      id: request.id,
      result: {
        content: [{ type: 'text', text: `当前时间: ${new Date().toLocaleString()}` }]
      }
    }
    console.log(JSON.stringify(response))
  }
})
```

这个服务器只有一个工具——获取当前时间。但它展示了 MCP 的核心思想：通过标准输入/输出通信，用 JSON 交换数据。

下一章，我们将了解 Hook 系统——用户自定义的"触发器"。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
