# 第12章：工具的世界——从设计到实现

## AI 为什么需要工具？

纯粹的 AI 对话只能"说话"——它能给你建议、解释概念、甚至写出代码片段。但它不能**真正做事**：它不能读你电脑上的文件，不能运行命令，不能修改代码。

工具改变了这一切。通过工具，AI 可以：
- 读取你的代码文件
- 搜索项目中的关键字
- 执行终端命令
- 修改文件内容
- 甚至打开网页查找信息

这就像给一个很聪明但只能说话的人配了一双手——现在它不仅能说"你应该这样改"，还能直接帮你改。

## 工具是怎么工作的？

AI 模型本身并不能执行代码。"工具"的工作方式是一种**协作机制**：

```
1. 程序告诉 AI："你有这些工具可以用"（发送工具定义）
2. AI 根据需要决定："我需要用 FileRead 工具"（发送工具调用）
3. 程序执行工具操作（读取文件）
4. 程序把结果告诉 AI（发送工具结果）
5. AI 根据结果继续回复
```

AI 不是自己执行工具——它只是"请求"程序执行，然后根据结果继续工作。就像一个医生不是自己做化验，而是让护士去做化验，然后根据化验结果给诊断。

## 工具的统一接口

Claude Code 有 40 多个工具，但它们都���循同一个接口：

```typescript
type Tool<Input, Output, Progress> = {
  // === 身份 ===
  name: string              // 工具名
  aliases?: string[]        // 别名

  // === 核心功能 ===
  call(input, context): Promise<ToolResult<Output>>   // 执行
  inputSchema: ZodSchema    // 输入格式定义
  description(): string     // 工���说明（给 AI 看的）

  // === 权限 ===
  checkPermissions(input, context): Promise<PermissionResult>

  // === 安全属性 ===
  isConcurrencySafe(input): boolean   // 能并行执行吗？
  isReadOnly(input): boolean           // 只读操作吗？
  isDestructive(input): boolean        // 有破坏性吗？

  // === 显示 ===
  renderToolUseMessage(input): ReactNode      // 调用时显示什么
  renderToolResultMessage(output): ReactNode  // 结果显���什么
}
```

让我们逐一理解这些属性：

### name——工具的名字

```typescript
name: "Bash"        // 终端命令工具
name: "FileRead"    // 文件读取工具
name: "FileEdit"    // 文件编辑工具
```

AI 通过名字来"调用"工具。

### inputSchema——输入格式

每个工具都精确定义了它接受什么输入：

```typescript
// Bash 工具的输入
const BashInputSchema = z.object({
  command: z.string().describe("要执行的 shell 命令"),
  timeout: z.number().optional().describe("超时时间（毫秒）"),
})

// FileRead 工具的输入
const FileReadInputSchema = z.object({
  file_path: z.string().describe("文件的绝对路径"),
  offset: z.number().optional().describe("从第几行开始读"),
  limit: z.number().optional().describe("读取多少行"),
})
```

这些 schema 有两个作用：
1. **告诉 AI** 每个参数是什么、怎么用
2. **验证输入** 确保 AI 传的参数格式正确

### call——执行函数

这是工具的核心——真正干活的部分：

```typescript
async call(input, context) {
  // 1. 验证输入
  // 2. 执行操作
  // 3. 返回结果
}
```

### 安全属性

三个布尔值告诉系统这个工具的"安全等级"：

```typescript
// FileRead 工具
isConcurrencySafe: true    // 可以同时读多个文件
isReadOnly: true            // 只读，不会改变什么
isDestructive: false        // 不会删除或破坏

// Bash 工具
isConcurrencySafe: false   // 可能有副作用，不能并行
isReadOnly: false           // 可能修改文件
isDestructive: true         // 可能删除文件
```

这些属性影响：
- 能否并行执行
- 是否需要权限检��
- 用户中断时的处理方式

## buildTool：工具的工厂函数

所有工具都通过 `buildTool()` 函数创建，它提供了合理的默认值：

```typescript
const TOOL_DEFAULTS = {
  isEnabled: () => true,              // 默认启用
  isConcurrencySafe: () => false,      // 默认不能并行（保守）
  isReadOnly: () => false,             // 默认非只读（保守）
  isDestructive: () => false,          // 默认无破坏性
  checkPermissions: () => ({ behavior: "allow" }),  // 默认允许
}
```

注意默认值的设计哲学：**宁可保守，不可冒险。**

`isConcurrencySafe` 默认是 `false`——如果一个工具忘了声明自己是并行安全的，系统会按串行执行，最多就是慢一点，不会出错。

如果默认是 `true`，一个不安全的工具忘了声明，就可能并行执行导致数据损坏。

这叫做 **fail-safe design（故障安全设计）**——系统的默认行为应该是安全的。

## 工具注册中心

所有工具在 `tools.ts` 中注册：

```typescript
export function getAllBaseTools(): Tool[] {
  return [
    // 核心工具（总是可用）
    AgentTool,
    BashTool,
    FileReadTool,
    FileEditTool,
    FileWriteTool,
    GlobTool,
    GrepTool,
    WebFetchTool,
    WebSearchTool,
    NotebookEditTool,
    SkillTool,

    // 条件工具（需要特定环境）
    ...(isTaskV2Enabled()
      ? [TaskCreateTool, TaskUpdateTool, TaskGetTool, TaskListTool]
      : []),

    ...(isWorktreeEnabled()
      ? [EnterWorktreeTool, ExitWorktreeTool]
      : []),

    ...(isLSPEnabled()
      ? [LSPTool]
      : []),

    // ... 更多条件工具
  ]
}
```

条件注册确保了：
- 只有需要的工具才会被加载
- 新功能可以通过开关控制发布
- 不同环境（Windows/Mac/Linux）有不同的工具集

## 工具池的组装

最终发送给 AI 的工具列表经过几层过滤：

```
所有工具（40+）
    │
    ▼
过滤：isEnabled() === true
    │ （排除被禁用的工具）
    ▼
过滤：移除被 deny 规则禁止的工具
    │ （管理员或用户配置的黑名单）
    ▼
添加：MCP 工具
    │ （来自外部服务器的工具）
    ▼
去重：同名工具保留内置版本
    │
    ▼
排序：按名字排序
    │ （保持顺序稳定，提高缓存命中率）
    ▼
最终工具池（发送给 AI）
```

为什么要按名字排序？因为工具定义是系统提示词的一部分，如果工具顺序变了，提示缓存就失效了，导致每次都要重新付费。

## 延迟加载：ToolSearch

当工具太多时，每次都把所有工具的定义发给 AI 很浪费 token。Claude Code 有一个聪明的方案——**延迟加载**：

```
初始请求时：
  总是发送：Bash, FileRead, FileEdit, FileWrite, Grep, Glob
  延迟发送：LSP, CronCreate, WebBrowser, 等 30+ 工具

当 AI 需要某个延迟工具时：
  AI 调用 ToolSearch("cron schedule")
  → 系统返回 CronCreateTool 的定义
  → 下一轮 AI 就可以使用 CronCreateTool 了
```

这就像你的手机只显示最常用的 App，其他的需要在搜索里找。

## 工具执行的完整流��

```
AI 发送工具调用请求
    │
    ▼
1. 查找工具
   工具名 → 在注册表中查找 → 找到工具对象
    │
    ▼
2. 输入验证
   tool.inputSchema.safeParse(input)
   → 格式正确吗？类型对吗？
    │
    ▼
3. 运行前置钩子
   preToolUseHooks → 可以修改输入或拒绝执行
    │
    ▼
4. 权限检查
   tool.checkPermissions(input)
   → 用户允许这个操作吗？
    │
    ▼
5. 执行工具
   tool.call(input, context)
   → 实际执行操作
    │
    ▼
6. 运行后置钩子
   postToolUseHooks → 可以修改结果
    │
    ▼
7. 格式化结果
   tool.mapToolResultToToolResultBlockParam()
   → 转换为 API 格式
    │
    ▼
8. 返回给 AI
```

每一步都有可能失败，每一步都有错误处理。这种"层层把关"的设计确保了系统的健壮性。

## 本章小结

- 工具让 AI 从"只能说"变成"能做事"
- 所有工具遵循统一接口：name、call、inputSchema、权限检查等
- **故障安全设计**：默认值总是保守的（不能并行、非只读、需要���限）
- `buildTool()` 工厂函数提供合理的默认值
- 工具注册支持条件加载（根据环境和功能开关）
- 工具池经过多层过滤和排序
- **延迟加载**减少不必要的 token 消耗
- 工具执行有 8 个步骤：查找 → 验证 → 钩子 → 权限 → 执行 → 钩子 → 格式化 → 返回

## 思考题

1. 为什么所有工具要遵循统一接口？如果每个工具自己定义接口会怎样？
2. "故障安全设计"在日常生活中有什么例子？（提示：电梯、安全带）
3. 如果你要设计一个新工具（比如"翻译工具"），它的 inputSchema 应该怎么定义？

## 真实世界的类比

工具系统的设计让我想到了**USB 接口**的故事。

在 USB 发明之前，电脑上的外设各自使用不同的接口：打印机用并口、鼠标用 PS/2 口、调制解调器用串口……每种设备都需要专门的接口和驱动程序。

USB（Universal Serial Bus，通用串行总线）改变了这一切。它定义了一个**统一的接口标准**：

- 物理接口统一（USB 插头）
- 通信协议统一（USB 协议）
- 供电方式统一（USB 供电）

只要设备实现了 USB 协议，就可以插到任何 USB 口上使用。不需要关心具体是什么设备。

Claude Code 的工具系统就是软件世界的"USB"：
- `Tool` 接口就是"USB 插头"——所有工具都必须遵循
- `call()` 方法就是"USB 协议"——统一的执行方式
- `inputSchema` 就是"设备描述"——告诉系统这个工具需要什么输入

这种"一个标准连接一切"的设计，在软件工程中叫做**面向接口编程**——它让系统可以不断扩展新的工具，而不需要修改核心代码。

接下来三章，我们将深入具体的工具实现。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
