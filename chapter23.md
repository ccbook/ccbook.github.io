# 第23章：插件与技能——无限扩展

## 两种扩展方式

Claude Code 提供了两种扩展方式：

| | 插件（Plugin） | 技能（Skill） |
|---|---|---|
| 复杂度 | 高（需要写代码） | 低（只需要写文本） |
| 能力 | 可以添加工具、命令、UI | 只能添加提示词和工作流 |
| 分发 | 通过 npm 安装 | 放在目录里就行 |
| 适合 | 开发者 | 所有人 |

## 技能系统（Skills）

技能是 Claude Code 最简单的扩展方式——你只需要写一个 Markdown 文件，就能教 AI 新的"技能"。

### 创建一个技能

在 `~/.claude/skills/` 目录下创建一个文件：

```markdown
# ~/.claude/skills/code-review.md

---
name: code-review
description: 进行详细的代码审查
---

你现在是一个严格的代码审查专家。请审查提供的代码，检查以下方面：

## 代码质量
- 命名是否清晰（变量名、函数名）
- 函数是否过长（超过 30 行应该拆分）
- 是否有重复代码

## 安全性
- 是否有 SQL 注入风险
- 是否正确处理了用户输入
- 是否有硬编码的密钥

## 性能
- 是否有不必要的循环
- 是否有 N+1 查询问题
- 是否正确使用了缓存

请用以下格式输出审查结果：
- 严重问题用 🔴 标记
- 警告用 🟡 标记
- 建议用 🟢 标记
```

### 使用技能

有两种方式调用技能：

```
方式 1：斜杠命令
/skill code-review

方式 2：直接提及
"请用 code-review 技能审查 src/api.ts"
```

### 技能的发现

AI 可以自动发现并推荐技能：

```
用户: "帮我审查一下这个 PR"

AI 思考：用户想做代码审查...
         我有一个 code-review 技能可以用！

AI: "我发现有一个 code-review 技能可以帮助你。要我用它来审查吗？"
```

### 技能的组合

技能可以互相组合：

```markdown
# ~/.claude/skills/full-review.md

---
name: full-review
description: 完整的代码审查流程
---

请按以下步骤进行完整的代码审查：

1. 首先用 /skill code-review 检查代码质量
2. 然后用 /skill security-scan 检查安全问题
3. 最后用 /skill performance-check 检查性能
4. 汇总所有发现，生成一份报告
```

## 插件系统（Plugins）

插件是更强大的扩展方式——它们可以用代码来扩展 Claude Code 的功能。

### 插件的结构

```typescript
// 一个插件的基本结构
export type Plugin = {
  id: string              // 唯一标识
  name: string            // 显示名称
  version: string         // 版本号
  description: string     // 描述

  commands?: Command[]    // 新增的斜杠命令
  tools?: Tool[]          // 新增的工具
  hooks?: Hook[]          // 新增的钩子
}
```

### 插件能做什么？

**1. 添加新工具**

```typescript
// 翻译工具插件
const TranslateTool = buildTool({
  name: "Translate",
  inputSchema: z.object({
    text: z.string(),
    from: z.string(),
    to: z.string(),
  }),
  async call(input) {
    const result = await translateAPI(input.text, input.from, input.to)
    return { data: result }
  },
  description: () => "翻译文本",
})
```

**2. 添加新命令**

```typescript
// 代码统计命令插件
const StatsCommand = {
  name: "stats",
  help: "显示代码统计信息",
  async handler(input, context) {
    const stats = await analyzeCodebase()
    context.displayMessage({
      role: "system",
      content: `项目统计：
        文件数: ${stats.files}
        总行数: ${stats.lines}
        语言分布: ${stats.languages.join(", ")}`,
    })
  },
}
```

**3. 添加钩子**

```typescript
// 自动格式化钩子
const AutoFormatHook = {
  event: "PostToolUse",
  matcher: "FileEdit",
  async handler(context) {
    const filePath = context.toolInput.file_path
    await formatFile(filePath)
  },
}
```

### 插件的安装

```bash
# 从 npm 安装
claude plugin install @company/claude-translate-plugin

# 插件安装到 ~/.claude/plugins/
```

### 插件的安全

插件运行在受限环境中，有以下限制：

```
✅ 可以读取工作目录内的文件
✅ 可以调用网络 API
✅ 可以注册工具和命令

❌ 不能直接修改文件（必须通过工具系统）
❌ 不能绕过权限检查
❌ 不能访问其他插件的数据
```

## 技能 vs 插件 vs MCP

三种扩展方式各有适用场景：

```
简单的提示词模板？→ 用技能
  例：代码审查模板、提交信息格式

需要自定义逻辑？→ 用插件
  例：代码统计工具、自动翻译工具

需要连接外部服务？→ 用 MCP
  例：数据库查询、Slack 集成、GitHub API
```

它们也可以组合使用：

```
MCP 提供数据库查询能力
  + 插件提供查询结果可视化
  + 技能定义何时使用什么查询
  = 一个完整的数据库助手
```

## 扩展生态系统

Claude Code 的三种扩展方式形成了一个生态系统：

```
┌─────────────────────────────────────────────┐
│                Claude Code 核心               │
│                                              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │  技能 A   │ │  技能 B   │ │  技能 C   │   │
│   │(Markdown) │ │(Markdown) │ │(Markdown) │   │
│   └──────────┘ └──────────┘ └──────────┘   │
│                                              │
│   ┌──────────┐ ┌──────────┐                 │
│   │  插件 A   │ │  插件 B   │                 │
│   │  (代码)   │ │  (代码)   │                 │
│   └──────────┘ └──────────┘                 │
│                                              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│   │ MCP 服务A │ │ MCP 服务B │ │ MCP 服务C │   │
│   │  (进程)   │ │  (进程)   │ │  (进程)   │   │
│   └──────────┘ └──────────┘ └──────────┘   │
│                                              │
└─────────────────────────────────────────────┘
```

## 本章小结

- **技能**是最简单的扩展——一个 Markdown 文件就能教 AI 新能力
- **插件**可以用代码添加工具、命令和钩子
- **MCP** 连接外部服务和 API
- 三种方式各有适用场景，可以组合使用
- 插件运行在受限环境中，不能绕过安全系统

## 思考题

1. 如果你是一个高中生开发者，你会创建什么样的技能？
2. 插件系统的安全限制是否足够？你能想到什么潜在风险吗？
3. 技能、插件、MCP 三者的边界在哪里？一个功能应该用哪种方式实现？

## 扩展性的三个层次

Claude Code 的扩展系统展示了"扩展性"的三个层次：

```
第一层：配置级扩展（最简单）
  改 settings.json 就能自定义行为
  例：修改权限规则、改主题、改快捷键
  → 不需要写任何代码

第二层：内容级扩展（中等）
  写 Markdown 文件就能添加新功能
  例：创建技能文件、编写 CLAUDE.md
  → 需要写文本，但不需要写代码

第三层：代码级扩展（最灵活）
  写代码来实现任何功能
  例：开发插件、编写 MCP 服务器
  → 需要编程技能
```

好的系统应该让不同水平的用户都能扩展它。初学者可以改配置，中级用户可以写技能文件，高级用户可以开发插件。

这种"阶梯式"的扩展设计让系统对新手友好、对专家强大。

下一章，我们将进入高级话题篇——多智能体协作。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
