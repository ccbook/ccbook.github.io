# 附录 A：术语表

本附录收录了书中出现的专业术语，按字母顺序排列。

## A

**Agent Loop（智能体循环）**：AI 不断重复"思考 → 行动 → 观察"的过程，直到任务完成。这是 Claude Code 查询引擎的核心模式。参见第 9 章。

**ANSI 转义码**：一种特殊字符序列，用于在终端中控制文字的颜色、样式和位置。比如 `\x1b[31m` 表示切换到红色。参见第 5 章。

**API（Application Programming Interface）**：应用程序编程接口。一组规定好的规则，让不同的程序可以互相通信。Claude API 就是 Claude AI 的接口。

**async/await**：JavaScript/TypeScript 中处理异步操作的语法。`async` 标记函数是异步的，`await` 等待异步操作完成。参见第 3 章。

## B

**Bash**：一种 Unix shell 程序，也是 Claude Code 中最强大的工具之一。通过它可以执行终端命令。参见第 13 章。

**Bridge（桥接）**：连接 IDE 和 Claude Code 的通信层。让 Claude Code 可以在 VS Code 等编辑器中运行。参见第 22 章。

## C

**Cache（缓存）**：把计算结果存储起来，下次需要时直接使用，避免重复计算。参见第 25 章。

**CLI（Command Line Interface）**：命令行界面。通过在终端输入文字命令来操作计算机，与图形界面（GUI）相对。

**Context Window（上下文窗口）**：AI 模型一次能"看到"的最大文本量。不同模型有不同的窗口大小（200K-1M tokens）。参见第 11 章。

**Component（组件）**：React 的基本构建单位。一个组件就是一段可复用的界面代码。参见第 5 章。

## D

**Diff**：两个文本版本之间的差异。通常用红色表示删除，绿色表示新增。

**Defense in Depth（纵深防御）**：多层安全防护策略。即使某一层被绕过，其他层仍然能保护系统。参见第 19 章。

## E

**Event-Driven（事件驱动）**：程序通过响应"事件"来执行操作，而不是按固定顺序执行。参见第 28 章。

**Exponential Backoff（指数退避）**：一种重试策略。每次失败后，等待时间翻倍。避免所有请求同时重试导致服务器过载。参见第 9 章。

## F

**Fail-Safe（故障安全）**：当系统出错时，自动进入安全状态。比如默认拒绝不确定的操作。参见第 12 章。

**Feature Flag（功能开关）**：控制某个功能是否启用的开关。允许渐进式发布新功能。参见第 4 章。

**Flexbox**：一种 CSS 布局模式。Ink 框架在终端中也使用 flexbox 来排列元素。

## G

**Generator（生成器）**：一种可以"暂停"和"恢复"的函数。用 `function*` 定义，用 `yield` 输出值。参见第 3 章。

**Glob**：一种文件名匹配模式。`*` 匹配任意字符，`**` 匹配任意层目录。参见第 15 章。

**GrowthBook**：一种功能开关管理平台。Claude Code 用它来控制新功能的发布。参见第 27 章。

## H

**Hook（钩子）**：
1. React 中以 `use` 开头的函数（如 `useState`、`useEffect`），用于在组件中添加功能。
2. Claude Code 中用户定义的脚本，在特定事件发生时自动执行。参见第 21 章。

## I

**Ink**：一个让 React 在终端中运行的框架。用 `<Box>`、`<Text>` 等组件替代 HTML 元素。参见第 5 章。

**Interface（接口）**：定义一组方法签名的规范。实现接口的类必须提供这些方法。参见第 12 章。

## J

**JSON（JavaScript Object Notation）**：一种轻量级的数据格式。`{"key": "value"}` 就是 JSON。

**JWT（JSON Web Token）**：一种安全令牌，用于身份验证。Claude Code 的 IDE 桥接使用 JWT。参见第 22 章。

## L

**LRU（Least Recently Used）**：最近最少使用。一种缓存淘汰策略——当缓存满了，淘汰最久没用过的条目。参见第 25 章。

## M

**MCP（Model Context Protocol）**：模型上下文协议。一个让 Claude Code 连接外部工具的标准协议。参见第 20 章。

**MDM（Mobile Device Management）**：移动设备管理。企业用来统一管理员工设备配置的技术。

## P

**Promise**：JavaScript 中表示"未来的值"的对象。异步操作返回 Promise，完成后可以获取结果。参见第 3 章。

**Prompt Caching（提示缓存）**：缓存系统提示词等不变内容，避免重复处理。节省约 90% 的 token 费用。参见第 11 章。

## R

**React**：一个用于构建用户界面的框架。核心思想是"声明式"——你描述界面应该是什么样的，React 负责更新。

**REPL（Read-Eval-Print Loop）**：读取-评估-打印循环。交互式编程环境的经典模式。Claude Code 的默认模式就是一个 REPL。

**ripgrep（rg）**：一个用 Rust 编写的超快搜索工具。Claude Code 的 Grep 工具底层使用 ripgrep。

## S

**Sandbox（沙箱）**：一个受限的执行环境。命令在沙箱中运行，不能访问系统的其他部分。参见第 19 章。

**Schema**：数据的结构定义。描述数据应该是什么格式、有哪些字段、字段是什么类型。

**SSE（Server-Sent Events）**：一种 HTTP 协议扩展。服务器可以持续发送数据给客户端，用于流式响应。参见第 10 章。

**Streaming（流式）**：数据一小块一小块地传输和处理，而不是等全部完成才传输。参见第 10 章。

## T

**Token**：AI 模型处理文本的基本单位。大约 4 个英文字符或 1.5 个中文字符 = 1 个 token。

**TypeScript**：JavaScript 的超集，添加了静态类型系统。Claude Code 完全用 TypeScript 编写。

## W

**WebSocket**：一种全双工通信协议。服务器和客户端可以随时互相发送消息。

**Worktree（工作树）**：Git 的一个功能，允许同一个仓库同时有多个工作目录。参见第 16 章。

## Z

**Zod**：一个 TypeScript 运行时类型验证库。用于在程序运行时检查数据格式是否正确。参见第 3 章。

**Zustand**：一个轻量级的 React 状态管理库。Claude Code 用它管理全局状态。参见第 6 章。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
