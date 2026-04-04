# 第28章：架构之美——设计模式总结

## 回顾这段旅程

我们已经走过了 27 章的旅程，从程序入口到查询引擎，从工具系统到安全防线，从 MCP 协议到多智能体协作。现在是时候"站在山顶上"回头看看整个风景了。

在这一章中，我们将提炼出 Claude Code 源码中反复出现的**设计模式**——这些模式不仅适用于 Claude Code，也适用于你将来写的任何大型程序。

## 模式一：统一接口（Uniform Interface）

**哪里用到了？** 所有工具都遵循 `Tool<Input, Output, Progress>` 接口。

```typescript
// 40+ 个工具，同一个接口
type Tool = {
  name: string
  call(input): Promise<ToolResult>
  inputSchema: ZodSchema
  checkPermissions(input): Promise<PermissionResult>
  // ...
}
```

**为什么这样设计？**

想象如果每个工具有自己的接口：

```typescript
// 混乱的设计
bash.execute(command)           // Bash 用 execute
fileReader.open(path)           // FileRead 用 open
grep.search(pattern, directory) // Grep 用 search
```

调用者需要知道每个工具的特殊方法。每加一个工具，调用代码就要改一次。

统一接口意味着：

```typescript
// 整洁的设计
for (const tool of tools) {
  const result = await tool.call(input)  // 所有工具用同一个方法
}
```

调用者不需要知道具体是哪个工具——它们都长一样。这就是**多态**的力量。

**生活比喻：** 所有电器都用相同的插头标准。你不需要为台灯、电脑、冰箱分别安装不同的插座。

## 模式二：分层架构（Layered Architecture）

**哪里用到了？** 整个项目的目录组织。

```
UI 层      → components/
命令层     → commands/
查询层     → query.ts
工具层     → tools/
服务层     → services/
状态层     → state/
基础设施层 → utils/
```

**为什么这样设计？**

分层让每一层只关心自己的事情：
- UI 层不知道（也不需要知道）API 是怎么调用的
- 工具层不知道（也不需要知道）界面是怎么画的
- 每一层通过明确的接口与相邻层通信

好处：如果你想把终端界面换成网页界面，只需要改 UI 层，其他六层不用动。

**生活比喻：** 一栋大楼的每层有不同的功能——地下室是停车场，一楼是大厅，二楼是办公室。改装一楼的大厅不影响二楼的办公室。

## 模式三：故障安全（Fail-Safe Defaults）

**哪里用到了？** 工具的默认安全属性。

```typescript
const TOOL_DEFAULTS = {
  isConcurrencySafe: () => false,  // 默认不安全
  isReadOnly: () => false,          // 默认可写
  isDestructive: () => false,       // 默认不危险
}
```

**为什么这样设计？**

如果默认是"安全的"（`isConcurrencySafe: true`），那么一个忘了设置这个属性的新工具可能被错误地并行执行，导致数据损坏。

如果默认是"不安全的"（`isConcurrencySafe: false`），忘了设置的工具只会被串行执行——稍慢，但不会出错。

**原则：当你不确定时，选择安全的选项。**

**生活比喻：** 电梯在断电时会自动下到一楼并打开门（安全状态），而不是停在半空中关着门。

## 模式四：事件驱动（Event-Driven）

**哪里用到了？** Hook 系统、流式响应处理、状态更新。

```typescript
// 事件发生 → 触发处理函数
hooks.on("PreToolUse", (event) => { ... })
hooks.on("PostToolUse", (event) => { ... })
hooks.on("SessionEnd", (event) => { ... })
```

**为什么这样设计？**

事件驱动让系统高度可扩展——你可以在任何事件上"挂载"新的行为，而不需要修改核心代码。

想加一个"每次文件修改后自动格式化"的功能？不用改文件编辑的代码，只需要在 `PostToolUse` 事件上挂一个 Hook。

**生活比喻：** 订阅制——你订阅了"新包裹到达"的通知，有新包裹时你会收到通知，而不需要每小时去快递站检查一次。

## 模式五：生产者-消费者（Producer-Consumer）

**哪里用到了？** 流式响应处理。

```
API（生产者）→→→ 事件流 →→→ UI（消费者）
      │                         │
  一个字一个字地                 收到一个字
  生产文本                       就显示一个字
```

**为什么这样设计？**

生产者和消费者速度不同——API 生成文本的速度和终端渲染的速度不一样。通过事件流作为"缓冲区"，两边可以以各自的速度工作。

**生活比喻：** 餐厅的厨房和服务员。厨房（生产者）做好一道菜就放到出菜口，服务员（消费者）从出菜口取菜送给客人。厨房不需要等服务员回来才做下一道菜。

## 模式六：策略模式（Strategy Pattern）

**哪里用到了？** 权限决策、沙箱选择、重试策略。

```typescript
// 不同的权限模式是不同的"策略"
if (mode === "default") {
  strategy = new DefaultPermissionStrategy()
} else if (mode === "auto") {
  strategy = new AutoPermissionStrategy()
} else if (mode === "bypass") {
  strategy = new BypassPermissionStrategy()
}

// 使用策略
const decision = await strategy.checkPermission(tool, input)
```

**为什么这样设计？**

策略模式让你可以在运行时切换算法。用户选择不同的权限模式，本质上是选择了不同的权限检查策略。

**生活比喻：** GPS 导航让你选择"最快路线"、"最短路线"或"避开高速"——不同的路由策略，同一个目的地。

## 模式七：纵深防御（Defense in Depth）

**哪里用到了？** 整个安全系统。

```
第一层：AI 的自我约束
第二层：工具级验证
第三层：权限规则
第四层：AI 分类器
第五层：用户确认
第六层：沙箱隔离
```

**为什么这样设计？**

任何单一的安全措施都可能被绕过。多层防御确保即使某一层失败，其他层仍然能保护系统。

**生活比喻：** 银行的安全系统——大门、摄像头、保安、保险柜、密码锁、报警器。小偷可能骗过其中一个，但不太可能骗过所有。

## 模式八：缓存策略（Caching Strategy）

**哪里用到了？** 提示缓存、文件缓存、工具 schema 缓存。

```
提示缓存：系统提示词不变 → 重用缓存 → 节省 90% 费用
文件缓存：LRU 策略 → 最近读过的文件不重复读取
Schema 缓存：工具定义不变 → 不重复生成 JSON Schema
```

**核心原则：** 如果一个计算的输入没有变化，就不需要重新计算。

**生活比喻：** 你每天走同一条路上学，不需要每次都打开地图导航。记住一次路线，以后直接走。

## 模式九：渐进增强（Progressive Enhancement）

**哪里用到了？** 功能开关、条件加载。

```typescript
// 基础功能总是可用
const tools = [Bash, FileRead, FileEdit]

// 高级功能根据条件添加
if (feature('VOICE_MODE')) tools.push(VoiceTool)
if (feature('WEB_BROWSER')) tools.push(BrowserTool)
if (feature('LSP_INTEGRATION')) tools.push(LSPTool)
```

**为什么这样设计？**

不是所有用户都需要所有功能。基础功能保证可用，高级功能按需启用。这样：
- 新功能不会影响稳定性
- 启动速度不会因为功能增加而变慢
- 不同用户看到不同的功能集

## 模式十：关注点分离（Separation of Concerns）

这是贯穿整个项目的核心原则：

```
命令解析 vs 命令执行      → 分开
工具定义 vs 工具权限      → 分开
消息格式 vs 消息渲染      → 分开
状态存储 vs 状态使用      → 分开
安全规则 vs 安全执行      → 分开
```

每个模块只负责一件事。这让代码更容易理解、测试和修改。

## 本章小结

| 模式 | 核心思想 | Claude Code 中的例子 |
|------|---------|---------------------|
| 统一接口 | 所有组件遵循相同的接口 | 40+ 工具同一个 Tool 类型 |
| 分层架构 | 按职责分层，层间有明确接口 | UI → 命令 → 查询 → 工具 → 服务 |
| 故障安全 | 默认选择安全的选项 | 工具默认"不安全" |
| 事件驱动 | 通过事件解耦组件 | Hook 系统 |
| 生产者-消费者 | 异步的数据流 | 流式 API 响应 |
| 策略模式 | 运行时切换算法 | 权限模式选择 |
| 纵深防御 | 多层安全防护 | 六层安全系统 |
| 缓存策略 | 避免重复计算 | 提示缓存、LRU 缓存 |
| 渐进增强 | 基础功能保底，高级功能按需 | 功能开关系统 |
| 关注点分离 | 每个模块只做一件事 | 整个项目的组织方式 |

这些模式不是 Claude Code 独创的——它们是软件工程几十年积累的智慧。掌握这些模式，你就拥有了构建任何大型系统的基础。

## 模式的组合之美

在实际的系统中，模式很少单独出现——它们互相组合，形成更强大的设计。

比如 Claude Code 的工具执行流程就组合了多个模式：

```
统一接口 → 所有工具用同一个 call() 方法
  + 策略模式 → 不同的权限检查策略
  + 事件驱动 → Hook 在执行前后触发
  + 纵深防御 → 多层安全检查
  + 缓存策略 → 工具 schema 缓存
  = 一个既灵活又安全又高效的工具执行系统
```

设计模式就像乐高积木——每块积木很简单，但组合起来可以搭建出复杂精美的作品。

下一章，我们将从源码中提炼工程实践的启示。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
