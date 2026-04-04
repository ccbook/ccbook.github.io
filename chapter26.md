# 第26章：持久化记忆——跨会话的智慧

## AI 的"失忆"问题

每次你启动一个新的 Claude Code 会话，AI 都是一张白纸——它不记得你昨天和它讨论了什么、你的项目是做什么的、你喜欢什么编程风格。

这就像每天都遇到一个新同事，每次都要从头介绍自己和项目背景。很烦。

Claude Code 的记忆系统就是为了解决这个问题——**让 AI 跨会话记住重要的信息。**

## CLAUDE.md——项目的"说明书"

记忆系统的核心是一个叫 `CLAUDE.md` 的文件。它就像给 AI 准备的一份"项目说明书"：

```markdown
# CLAUDE.md

## 项目概述
这是一个在线书店的后端服务，使用 Express + TypeScript + PostgreSQL。

## 代码规范
- 使用 camelCase 命名变量和函数
- 使用 PascalCase 命名类和接口
- 每个函数不超过 30 行
- 必须写单元测试

## 常用命令
- `npm run dev` — 启动开发服务器
- `npm test` — 运行测试
- `npm run lint` — 代码检查

## 架构决策
- 2024-03 决定从 MongoDB 迁移到 PostgreSQL，原因是需要事务支持
- 2024-05 决定使用 Prisma 作为 ORM
- API 路由在 src/routes/ 目录下

## 已知问题
- 搜索功能在大量数据时较慢（see #234）
- 图片上传偶尔超时（see #256）
```

每次新会话开始时，Claude Code 会自动加载 `CLAUDE.md`，AI 就立刻了解了项目的背景。

## CLAUDE.md 的加载层次

`CLAUDE.md` 不只有一个——它有一个层次结构：

```
~/.claude/CLAUDE.md            全局记忆（所有项目通用）
  ↓ 合并
项目根目录/CLAUDE.md            项目级记忆
  ↓ 合并
项目根目录/.claude/CLAUDE.md    项目配置级记忆
  ↓ 合并
当前目录/CLAUDE.md              目录级记忆
```

每一层添加更具体的信息：

```
全局 CLAUDE.md：
  "我喜欢简洁的代码，不要过多注释"

项目 CLAUDE.md：
  "这是一个 React 项目，使用 TypeScript"

目录 CLAUDE.md：
  "这个目录是 API 路由，每个文件对应一个端点"
```

AI 最终看到的是所有层次合并后的信息。

## 嵌套记忆附件

CLAUDE.md 可以引用其他文件：

```markdown
## 架构文档
[Open: ./docs/architecture.md](./docs/architecture.md)

## API 规范
[Open: ./docs/api-spec.md](./docs/api-spec.md)
```

这些引用的文件会自动加载到 AI 的上下文中。这样你可以把详细的文档放在单独的文件里，CLAUDE.md 只作为"目录"。

## 自动记忆提取

Claude Code 可以在会话结束后自动提取关键信息并更新 CLAUDE.md：

```
会话中发生了什么：
  用户告诉 AI "我们刚从 React Router v5 迁移到 v6"
  AI 帮用户修改了路由代码
  用户提到 "以后的路由都用 v6 的 API"

自动提取的记忆：
  "2024-06 从 React Router v5 迁移到 v6，所有路由使用 v6 API"

自动更新 CLAUDE.md：
  ## 架构决策
  + - 2024-06 从 React Router v5 迁移到 v6，使用 v6 API
```

这样下次打开新会话时，AI 就知道要用 v6 的 API 写路由。

## 会话记录——完整的对话存档

除了 CLAUDE.md 的"精华记忆"，Claude Code 还保存了完整的会话记录：

```
~/.claude/sessions/
├── 2024-06-01-project-refactor.jsonl
├── 2024-06-02-bug-fix.jsonl
├── 2024-06-03-new-feature.jsonl
└── index.json  (索引文件)
```

每个 `.jsonl` 文件包含一次完整的对话：

```json
{"type":"user","content":"帮我重构用户模块","timestamp":1717200000}
{"type":"assistant","content":"好的，让我先看看...","timestamp":1717200005}
{"type":"tool_use","tool":"FileRead","input":{"path":"src/user.ts"},"timestamp":1717200006}
...
```

### /resume 命令

你可以用 `/resume` 命令恢复之前的会话：

```
$ /resume

最近的会话：
  1. [2024-06-03] 新功能开发 (45 条消息)
  2. [2024-06-02] Bug 修复 (23 条消息)
  3. [2024-06-01] 项目重构 (67 条消息)

选择要恢复的会话 (1-3):
```

恢复后，AI 就能看到之前的完整对话历史，仿佛你们从未分开。

## 记忆的存储结构

Claude Code 的记忆系统支持多种类型的记忆：

```
记忆类型
├── user       — 关于用户的信息（角色、偏好、技能水平）
├── feedback   — 用户的反馈（什么该做、什么不该做）
├── project    — 项目的信息（目标、决策、截止日期）
└── reference  — 外部资源的指针（文档链接、工具位置）
```

每种记忆存储为一个独立的 Markdown 文件：

```markdown
# ~/.claude/projects/myapp/memory/user_preferences.md

---
name: 用户编码偏好
description: Alice 的编码风格偏好
type: user
---

Alice 是一个有 3 年经验的前端开发者，偏好函数式编程风格。
不喜欢 class 组件，总是使用 hooks。
喜欢简洁的变量名，不喜欢过长的命名。
```

所有记忆文件在 `MEMORY.md` 中建立索引：

```markdown
# MEMORY.md

- [用户编码偏好](user_preferences.md) — Alice 的编码风格和习惯
- [项目技术栈](project_stack.md) — React + TypeScript + Prisma
- [反馈：测试习惯](feedback_testing.md) — 总是先写测试再写代码
```

## 记忆的更新策略

记忆不是一次写入永远不变的——它需要随时更新：

```
场景 1：用户提到新信息
  用户："我刚学了 Go 语言，以后可能会用到"
  → 更新 user 记忆：增加 "正在学习 Go"

场景 2：之前的信息过时了
  记忆中："项目使用 React 17"
  但 package.json 中已经是 React 18
  → 更新 project 记忆：React 17 → React 18

场景 3：用户给出反馈
  用户："不要在每个回复后面加总结"
  → 创建 feedback 记忆："不要在回复末尾添加总结"
```

## 记忆 vs 代码注释 vs Git 历史

| 什么信息 | 存在哪里 |
|---------|---------|
| 代码怎么工作的 | 代码本身（自文档化） |
| 为什么这样写 | 代码注释 |
| 什么时候由谁改的 | Git 历史 |
| 项目背景和决策 | CLAUDE.md 记忆 |
| 用户偏好和习惯 | 记忆文件 |

记忆系统存储的是**不在代码中但对 AI 很重要**的信息。代码规范、架构决策、用户偏好——这些东西代码本身无法传达。

## 本章小结

- **CLAUDE.md** 是 AI 的"项目说明书"，每次会话自动加载
- 记忆有层次：全局 → 项目 → 目录，逐层添加具体信息
- 嵌套附件让 CLAUDE.md 可以引用其他文档
- 自动记忆提取从对话中提取关键信息
- 会话记录保存完整对话，支持 `/resume` 恢复
- 四种记忆类型：user、feedback、project、reference
- 记忆需要持续更新以保持准确

## 记忆的哲学：什么值得记住？

设计记忆系统时，最难的问题不是"怎么存储"，而是"什么值得存储"。

Claude Code 的设计给出了一个清晰的答案：

**值得记住的：**
- 用户的偏好和习惯（不会变的）
- 项目的架构决策（不在代码中体现的）
- 用户的反馈（下次该做什么、不该做什么）

**不值得记住的：**
- 代码的具体内容（直接读文件就好）
- Git 历史（直接用 git log 就好）
- 临时的调试信息（只在当前会话有用）

这个原则可以用一句话概括：**只记住不能从其他地方获取的信息。**

如果信息在代码里 → 读代码
如果信息在 Git 里 → 查 Git
如果信息只在用户的脑子里 → 记到 CLAUDE.md

这种"能查就不存"的策略避免了记忆与现实不一致的问题——因为记忆可能过时，但"当场查到的信息"总是最新的。

下一章，我们将了解配置系统——让每个用户都有个性化的体验。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
