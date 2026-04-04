# 第14章：文件三剑客——Read、Write、Edit

## 三种工具，三种能力

Claude Code 提供了三个文件操作工具：

| 工具 | 能力 | 比喻 |
|------|------|------|
| **FileRead** | 读取文件内容 | 打开书来看 |
| **FileWrite** | 创建/覆写文件 | 写一本新书 |
| **FileEdit** | 修改文件的一部分 | 在书上做批注 |

为什么要三个工具而不是一个"万能文件工具"？因为**关注点分离**——每个工具做一件事，做好一件事。这让权限控制更精细：你可以允许 AI 读文件，但禁止它写文件。

## FileRead：读取文件

### 基本功能

```typescript
// AI 发出的读文件请求
{
  name: "FileRead",
  input: {
    file_path: "/Users/alice/project/src/app.ts",
    offset: 0,     // 从第几行开始（可选）
    limit: 2000,   // 读取多少行（可选）
  }
}
```

返回的结果带有行号：

```
1	import React from "react"
2	import { useState } from "react"
3
4	function App() {
5	  const [count, setCount] = useState(0)
6	  return <button onClick={() => setCount(count + 1)}>{count}</button>
7	}
```

行号很重要——当 AI 说"第 5 行有问题"时，你能直接找到对应的代码。

### 不只是文本

FileRead 不只能读文本文件。它支持多种格式：

```typescript
async function readFile(path: string) {
  const extension = getExtension(path)

  if (isImageFile(extension)) {
    // 图片文件 → 返回图片内容供 AI 视觉分析
    return { type: "image", data: readAsBase64(path) }
  }

  if (extension === ".pdf") {
    // PDF 文件 → 提取文本内容
    return { type: "document", text: extractPDFText(path, pages) }
  }

  if (extension === ".ipynb") {
    // Jupyter Notebook → 解析 cells 和输出
    return { type: "notebook", cells: parseNotebook(path) }
  }

  // 普通文本文件
  return { type: "text", content: readAsText(path) }
}
```

### 大文件处理

如果文件有 10 万行怎么办？一次性读取会占用太多 token。

```typescript
const DEFAULT_LINE_LIMIT = 2000  // 默认最多读 2000 行

if (!input.limit && fileLineCount > DEFAULT_LINE_LIMIT) {
  // 只读前 2000 行
  return readLines(path, 0, DEFAULT_LINE_LIMIT)
  // 并提示："文件有 100,000 行，只显示了前 2000 行。
  //          使用 offset 和 limit 参数来读取其他部分。"
}
```

AI 可以使用 `offset` 和 `limit` 来分批读取大文件：

```
第一次：read(path, offset=0, limit=2000)     → 第 1-2000 行
第二次：read(path, offset=2000, limit=2000)  → 第 2001-4000 行
...
```

## FileWrite：创建和覆写文件

### 基本功能

```typescript
{
  name: "FileWrite",
  input: {
    file_path: "/Users/alice/project/src/Button.tsx",
    content: "import React from 'react'\n\nfunction Button() {\n  return <button>Click me</button>\n}\n"
  }
}
```

FileWrite 会**完全覆盖**文件内容。如果文件已存在，旧内容会被替换。

### 安全检查

写文件之前，FileWrite 会做几项检查：

```typescript
async function checkBeforeWrite(path, content) {
  // 1. 路径检查：不能写到工作目录外面
  if (!isWithinWorkDir(path)) {
    throw new Error("不能写入工作目录之外的路径")
  }

  // 2. 敏感文件检查
  if (isSensitiveFile(path)) {
    // .env, credentials.json, private_key 等
    warn("警告：这个文件可能包含敏感信息")
  }

  // 3. 必须先读再写
  if (!hasBeenReadBefore(path) && fileExists(path)) {
    throw new Error("修改已有文件前必须先读取它")
  }

  // 4. 文件大小限制
  if (content.length > MAX_FILE_SIZE) {
    throw new Error("文件内容超过大小限制")
  }
}
```

特别注意第 3 点：**必须先读再写**。这是为了防止 AI 在不了解文件内容的情况下覆盖它。想象 AI 不小心覆盖了一个重要的配置文件——灾难！

## FileEdit：精确修改

FileEdit 是最精细的文件操作工具。它不是覆盖整个文件，而是**替换文件中的一段文字**：

```typescript
{
  name: "FileEdit",
  input: {
    file_path: "/Users/alice/project/src/app.ts",
    old_string: "const [count, setCount] = useState(0)",
    new_string: "const [count, setCount] = useState(10)",
  }
}
```

就像"查找替换"——找到 `old_string`，替换成 `new_string`。

### 为什么不用行号替换？

你可能会问：为什么不直接说"替换第 5 行"？

原因是：**行号会变**。如果你在第 3 行插入了一行新代码，原来的第 5 行就变成了第 6 行。用文本内容来定位比用行号更可靠。

### 唯一性要求

FileEdit 要求 `old_string` 在文件中是**唯一的**。如果有多个匹配，编辑会失败：

```typescript
function editFile(path, oldString, newString) {
  const content = readFile(path)

  // 检查匹配次数
  const matchCount = countOccurrences(content, oldString)

  if (matchCount === 0) {
    throw new Error("找不到要替换的文本")
  }

  if (matchCount > 1) {
    throw new Error(
      `找到 ${matchCount} 个匹配。请提供更多上下文使其唯一。`
    )
  }

  // 只有恰好 1 个匹配时才执行替换
  return content.replace(oldString, newString)
}
```

如果有多个匹配，AI 需要提供更多的上下文（比如包含上下几行）来确保唯一性。

### replace_all 模式

如果你确实想替换所有出现的地方（比如重命名变量），可以用 `replace_all`：

```typescript
{
  name: "FileEdit",
  input: {
    file_path: "src/app.ts",
    old_string: "myOldFunction",
    new_string: "myNewFunction",
    replace_all: true  // 替换所有出现的地方
  }
}
```

### 差异显示

编辑完成后，Claude Code 会显示一个漂亮的差异对比：

```diff
  src/app.ts
  ──────────
  function App() {
-   const [count, setCount] = useState(0)
+   const [count, setCount] = useState(10)
    return <button>{count}</button>
  }
```

红色（`-`）是被删除的，绿色（`+`）是新增的。这让用户一眼就能看到改了什么。

### 文件历史追踪

每次编辑都会被记录下来：

```typescript
fileHistoryTrackEdit({
  path: "src/app.ts",
  previousContent: "旧内容...",
  newContent: "新内容...",
  timestamp: Date.now(),
  editType: "FileEdit",
})
```

如果编辑出了问题，可以通过历史记录回退到之前的版本。

## 三个工具的协作

在实际使用中，三个工具经常配合使用：

```
场景：AI 修复一个 bug

1. FileRead("src/app.ts")
   → 看到完整的代码

2. FileRead("src/app.test.ts")
   → 看到测试用例，理解期望行为

3. FileEdit("src/app.ts", old, new)
   → 精确修改有 bug 的那一行

4. Bash("npm test")
   → 运行测试验证修复

5. 如果测试失败：
   FileRead("test-output.log")
   → 查看失败信息
   FileEdit("src/app.ts", old2, new2)
   → 再次修改

6. 如果需要新文件：
   FileWrite("src/utils/helper.ts", content)
   → 创建辅助函数
```

## 设计决策：为什么不用 Bash 来操作文件？

AI 完全可以用 Bash 来操作文件：`cat`（读）、`echo >`（写）、`sed`（编辑）。为什么还要专门的文件工具？

三个原因：

**1. 更精细的权限控制**

```
允许 FileRead，禁止 FileWrite
→ AI 可以看代码但不能改代码
```

用 Bash 做不到这种区分——`cat` 和 `echo >` 都是 Bash 命令。

**2. 更好的安全检查**

文件工具可以做专门的检查（路径验证、敏感文件检测、先读后写要求），Bash 做这些检查更困难。

**3. 更好的用户体验**

FileEdit 能显示漂亮的差异对比，FileRead 能显示行号。用 Bash 操作文件，输出就是纯文本。

## 本章小结

- **FileRead**：读文件，支持文本/图片/PDF/Notebook，大文件分批读取
- **FileWrite**：创建或覆写文件，必须先读后写，路径和敏感文件检查
- **FileEdit**：精确替换文本，要求唯一匹配，差异显示，历史追踪
- 三个工具分离是为了权限控制、安全检查和用户体验
- 文件操作有完整的历史记录，支持回退

## 文件操作的安全金字塔

从 FileRead 到 FileWrite，每个工具的"危险等级"递增，安全检查也递增：

```
                    ╱╲
                   ╱  ╲
                  ╱    ╲
                 ╱ Write ╲      ← 最危险：可能覆盖重要文件
                ╱  创建/覆写 ╲     安全检查：路径 + 敏感文件 + 先读后写
               ╱──────────────╲
              ╱                ╲
             ╱      Edit        ╲   ← 中等：修改文件的一部分
            ╱   精确替换文本      ╲    安全检查：唯一性 + 差异显示
           ╱────────────────────╲
          ╱                      ╲
         ╱         Read           ╲  ← 最安全：只看不改
        ╱     读取文件内容          ╲   安全检查：路径验证
       ╱────────────────────────────╲
```

这种分层设计让你可以给 AI 精细的权限：
- 只允许 Read → AI 只能看代码，不能改
- 允许 Read + Edit → AI 可以精确修改，但不能创建新文件
- 允许 Read + Edit + Write → AI 有完全的文件操作能力

**原则：给予完成任务所需的最小权限。**

下一章，我们将看看搜索工具：Grep 和 Glob。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
