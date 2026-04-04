# 第15章：搜索双雄——Grep 与 Glob

## 在大海捞针

想象你的项目有 1,000 ���文件，你想找到"某个函数在哪里定义的"或"有多少文件用了这个 API"。一个一个文件打开看？那得看到天荒地老。

这就是搜索工具的价值——它们帮你在海量文件中快速找到你要的东西。

Claude Code 有两个搜索工具，各有专长：

| 工具 | 搜索什么 | 比喻 |
|------|---------|------|
| **Grep** | 搜索文件**内容** | 在所有书里找某句话 |
| **Glob** | 搜索文件**名称** | 在图书馆找某本书 |

## Glob：按名字找��件

### 什么是 Glob？

"Glob" 这个词来自 Unix 系统的"全局匹配"（global）。它使用特殊的模式来匹配文件名。

```
*       匹配任意个字符       *.ts → app.ts, index.ts
**      匹配任意层目录       **/*.ts → src/app.ts, src/utils/helper.ts
?       匹配一个字符         file?.ts → file1.ts, fileA.ts
[abc]   匹配方括号内的字符   file[123].ts → file1.ts, file2.ts
```

### 使用示例

```typescript
// AI 调用 Glob 工具
{
  name: "Glob",
  input: {
    pattern: "src/**/*.tsx",     // 找所有 TSX 组件
    path: "/Users/alice/project"  // 在这个目录下搜索
  }
}

// 返回结果
[
  "src/App.tsx",
  "src/components/Button.tsx",
  "src/components/Header.tsx",
  "src/pages/Home.tsx",
  "src/pages/About.tsx",
]
```

### 实际场景

AI 经常用 Glob 来了解项目结构：

```
AI 想了解项目的测试文��：
→ Glob("**/*.test.ts")
→ ["src/app.test.ts", "src/utils/helper.test.ts", ...]

AI 想找所有配置文件：
→ Glob("**/config.*")
→ ["package.json", "tsconfig.json", ".eslintrc.json", ...]

AI 想找特定组件：
→ Glob("**/Button*")
→ ["src/components/Button.tsx", "src/components/Button.test.tsx", ...]
```

### 结果排序

Glob 返回的文件按**修改时间**排序——最近修改的排在前面。这很实用，因为你通常更关心最近改过的文件。

## Grep：搜索文件内容

### 基于 ripgrep

Grep 工具底层使用了 **ripgrep**（`rg` 命令）——一个用 Rust 写的超快搜索工具。ripgrep 比传统的 `grep` 命令快 10-100 倍，特别适合搜索大型项目。

### 使用示例

```typescript
// AI 调用 Grep 工具
{
  name: "Grep",
  input: {
    pattern: "function.*useState",  // 正则表达式
    path: "src/",
    type: "tsx",                     // 只搜索 tsx 文件
    output_mode: "content",          // 显示匹配的行内容
    context: 2,                      // 显示前后各 2 行上下文
  }
}

// 返回结果
// src/App.tsx
// 3: import { useState } from "react"
// 4:
// 5: function App() {
// 6:   const [count, setCount] = useState(0)  ← 匹配
// 7:   return <div>{count}</div>
```

### 三种输出模式

```typescript
// 模式 1: files_with_matches（默认）—— 只显示文件名
["src/App.tsx", "src/pages/Home.tsx"]

// 模式 2: content —— 显示匹配行的内容（带上下文）
"src/App.tsx:6:  const [count, setCount] = useState(0)"

// 模式 3: count —— 只显示每个文件的匹配数
"src/App.tsx: 3 matches"
"src/pages/Home.tsx: 1 match"
```

AI 会根据需要选择不同的模式：
- 只想知道"哪些文件有这个关键词" → `files_with_matches`
- 想看具体的代码 → `content`
- 想统计使用频率 → `count`

### 正则表达式

Grep 支持完整的正则表达式（和 ripgrep 一致）：

```
"useState"              精确匹配 "useState"
"use[A-Z]\\w+"          匹配所有 Hook（useEffect, useState, ...）
"function\\s+\\w+"      匹配所有函���定义
"TODO|FIXME|HACK"       匹配常见的代码标注
"import.*from.*react"   匹配 React 导入语句
```

正则表达式是一种强大的模式匹配语言。如果你还不熟悉，可以把它想象成一种"高级搜索语法"——比普通搜索灵活得多。

### 结果限制

为了避免返回太多结果（浪费 token），Grep 有一个默认限制：

```typescript
const DEFAULT_HEAD_LIMIT = 250  // 默认最多返回 250 行/条

// 用户可以覆盖
input.head_limit = 0  // 0 表示无限制（谨慎使用）
```

### 文件类型过滤

```typescript
// 按类型过滤（使用 ripgrep 的内置类型）
{
  type: "ts"   // 只搜索 TypeScript 文件
}
// 等同于搜索 *.ts, *.tsx 文件

// 按 glob 模式过滤
{
  glob: "*.{ts,tsx}"  // 更灵活的过滤
}
```

## Grep vs Glob：什么时候用哪个？

```
想知道 "哪里有 .config 文件？"
  → Glob("**/*.config.*")
  → 按文件名搜索

想知道 "哪里调用了 fetchData 函数？"
  → Grep("fetchData", type: "ts")
  → 按文件内容搜索

��知道 "测试目录里有什么？"
  → Glob("test/**/*")
  → 按文件结构浏览

想知道 "这个变���在哪里被修改了？"
  → Grep("myVariable\\s*=", output_mode: "content")
  → 按代码模式搜索
```

简单记忆：**Glob 找文件，Grep 找代码。**

## 为什么不直接用 Bash？

和文件工具一样，你可能会问：为什么不直接用 `bash find` 和 `bash grep`？

```bash
# 这样也能搜索
find . -name "*.ts"
grep -r "useState" src/
```

原因：

**1. 更安全**

Grep 和 Glob 工具被标记为"只读"和"并行安全"。系统可以放心地同时运行多个搜索，而不用担心副作用。Bash 命令不能做这种保证。

**2. 更快**

Grep 工具底层用 ripgrep，比 bash 的 grep 快得多。Glob 工具经过优化，直接调用 Node.js 的文件系统 API，不需要启动子进程。

**3. 更友好的输出**

搜索工具会格式化输出（添加行号、高亮、上下文），Bash 的输出是原始文本。

**4. 结果可控**

搜索工具有内置的结果限制（`head_limit`），不会一次返回几万行结果把 token 耗光。

## 搜索策略：AI 是怎么搜索的���

有趣的是，Claude Code 的系统提示词里教了 AI 怎么有效地搜索：

```
优先使用 Grep 搜索文件内容（而不是用 Bash 的 grep 或 rg 命令）
优先使用 Glob 搜索文���名（而不是用 Bash 的 find 或 ls 命令）
```

AI 通常的搜索策略是：

```
1. 先用 Glob 大致了解项目结构
   → Glob("src/**")  获取文件列表

2. 用 Grep 找到关键代码
   → Grep("functionName", type: "ts", output_mode: "files_with_matches")
   → 知道在哪些文件里

3. 用 FileRead 深入查看
   → FileRead("src/utils/helper.ts")
   → 阅读完整代码

4. 如果需要，用 Grep 找更多关联
   → Grep("helperFunction", output_mode: "content", context: 5)
   → 找到所有使用这个函数的地方
```

这种"由粗到细"的搜索策略非常高效。

## 本章小结

- **Glob** 按文件名模式搜索，支持 `*`、`**`、`?` 等通配符
- **Grep** 按内容搜索，���于 ripgrep，支持正则表达式
- Grep 有三种输出模式：文件名、内容、计数
- 专用搜索工具比 Bash 命令更安全、更快、输出更友好
- AI 的搜���策略：Glob 概览 → Grep 定位 → FileRead 深入

## 思考题

1. 用 Glob 模式写出以下搜索：
   - 找到所有 Python 文件
   - 找到 `src` 目录下所有测试文件
   - 找到名为 `index` 的任何类型的文件

2. 用 Grep 模式写出以下搜索：
   - 找到所有 `console.log` 语句
   - 找到所有 TODO 注释
   - 找到所有以 `use` 开头的函数定义

## 搜索能力的价值

你可能觉得"搜索"很简单——不就是 Ctrl+F 吗？

但在一个有 1,000 个文件的项目中，高效的搜索是一种**超能力**。考虑这个场景：

> "这个 API 端点返回 500 错误，我需要找到出错的代码。"

一个新手可能：
1. 猜测文件名，逐个打开查看（10 分钟）
2. 在每个文件里 Ctrl+F 搜索（15 分钟）
3. 可能还找不到

用 Grep + Glob 的搜索策略：
1. `Grep("500", type: "ts", output_mode: "files_with_matches")` → 2 秒
2. `Grep("throw.*Error", path: "src/api/")` → 2 秒
3. `FileRead("src/api/users.ts", offset: 40, limit: 10)` → 1 秒

**30 分钟的工作压缩到 5 秒。**

这就是为什么 Claude Code 要有专门的搜索工具，而且它们是 AI 最频繁使用的工具之一。对于 AI 来说，"理解代码"的第一步永远是"搜索代码"。

下一章，我们将探索最神奇的工具——Agent 工具，AI 的"分身术"。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
