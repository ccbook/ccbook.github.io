# 第27章：配置系统——千人千面

## 每个人都不一样

不同的开发者有不同的需求：

- 有人喜欢深色主题，有人喜欢浅色
- 有人希望 AI 自动执行命令，有人希望每次都确认
- 有人用 VS Code，有人用 JetBrains
- 公司的安全团队可能需要禁止某些危险操作

配置系统让每个用户都能按自己的方式使用 Claude Code。

## 配置的层次

Claude Code 的配置有严格的优先级层次：

```
最高优先级
    ↑
CLI 参数          claude --model opus
    │
环境变量          CLAUDE_API_KEY=sk-xxx
    │
管理员策略        managed-settings.json（IT 部门配置）
    │
用户设置          ~/.claude/settings.json
    │
MDM 策略          macOS/Windows 系统管理
    │
默认值            程序内置的默认值
    ↓
最低优先级
```

高优先级覆盖低优先级。这意味着：
- **CLI 参数总是胜出**：你在命令行指定了什么，就用什么
- **管理员可以强制执行策略**：即使用户修改了设置，管理员策略仍然生效
- **默认值是兜底**：如果什么都没配置，就用默认值

## settings.json 详解

用户设置保存在 `~/.claude/settings.json` 中：

```json
{
  // AI 模型选择
  "model": "claude-sonnet-4-20250514",

  // 权限配置
  "permissions": {
    "alwaysAllow": [
      "Bash(git *)",
      "Bash(npm test *)",
      "Bash(ls *)",
      "FileRead(*)"
    ],
    "alwaysDeny": [
      "Bash(rm -rf *)",
      "Bash(curl * | bash)"
    ],
    "alwaysAsk": [
      "Bash(git push *)",
      "Bash(npm publish *)"
    ]
  },

  // MCP 服务器
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["~/.mcp/github/index.js"],
      "env": { "GITHUB_TOKEN": "..." }
    }
  },

  // Hook 配置
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...]
  },

  // 界面设置
  "theme": "dark",

  // 快捷键
  "keybindings": {
    "submit": "enter",
    "newline": "shift+enter"
  }
}
```

## 管理员策略

在企业环境中，IT 管理员可能需要对所有开发者的 Claude Code 进行统一配置：

```json
// ~/.claude/managed-settings.json
{
  // 强制使用公司的 API 端点
  "apiBaseUrl": "https://api.company-internal.com/claude",

  // 禁止使用某些工具
  "permissions": {
    "alwaysDeny": [
      "Bash(curl *)",        // 禁止使用 curl
      "Bash(wget *)",        // 禁止使用 wget
      "WebFetch(*)",         // 禁止获取网页
      "WebSearch(*)"         // 禁止网络搜索
    ]
  },

  // 强制开启审计日志
  "auditLog": true,

  // 限制可用模型
  "allowedModels": ["claude-sonnet-4-20250514"]
}
```

管理员策略的优先级高于用户设置——用户**不能**覆盖管理员禁止的操作。

### MDM（移动设备管理）

在 macOS 上，公司可以通过 MDM（Mobile Device Management）分发配置。Claude Code 可以读取 MDM 配置：

```typescript
// macOS: 使用 plutil 读取 MDM 配置
const mdmConfig = await exec("plutil -p /Library/Managed Preferences/com.anthropic.claude-code.plist")

// Windows: 读取注册表
const regConfig = await exec("reg query HKLM\\Software\\Anthropic\\ClaudeCode")
```

这让大型企业能在数千台电脑上统一管理 Claude Code 的配置。

## 动态配置更新

配置不是静态的——它可以在程序运行时更新：

```typescript
// 监听 settings.json 的变化
watchFile("~/.claude/settings.json", () => {
  // 文件被修改了
  const newSettings = loadSettings()

  // 更新全局状态
  updateAppState({
    toolPermissionContext: newSettings.permissions,
    theme: newSettings.theme,
    // ...
  })

  // 重新注册工具和命令
  refreshToolPool()
  refreshCommands()
})
```

当你用文本编辑器修改 `settings.json` 并保存时，Claude Code 会自动检测到变化并应用新配置——不需要重启程序。

## GrowthBook 功能开关

除了用户配置，Claude Code 还有一套内部的功能开关系统——**GrowthBook**：

```typescript
// 检查功能开关
if (feature('VOICE_MODE')) {
  // 加载语音功能
}

if (feature('WEB_BROWSER_TOOL')) {
  // 启用浏览器工具
}

if (feature('AGENT_TRIGGERS')) {
  // 启用定时任务功能
}
```

功能开关由 Anthropic 的服务器控制。这让开发团队可以：

1. **渐进式发布**：先对 1% 的用户开放新功能，观察效果后逐步扩大
2. **A/B 测试**：给一半用户看版本 A，另一半看版本 B，比较哪个更好
3. **紧急关闭**：如果新功能有 bug，可以立刻关闭，不需要发布新版本

```
功能发布流程：
  开发完成 → 1% 用户测试 → 10% 用户 → 50% 用户 → 100% 用户
                                              ↑
                                        发现问题？立刻关闭
```

## 配置迁移

随着 Claude Code 版本更新，配置格式可能会变化。`migrations/` 目录处理配置格式的升级：

```typescript
// 从 v1 格式迁移到 v2 格式
function migrateV1toV2(oldConfig) {
  return {
    ...oldConfig,
    // v1 用 "allowedTools"，v2 改为 "permissions.alwaysAllow"
    permissions: {
      alwaysAllow: oldConfig.allowedTools || [],
    },
    // 删除旧字段
    allowedTools: undefined,
  }
}
```

这确保老版本的配置文件在新版本中仍然能工作。用户不需要手动修改配置——升级时自动迁移。

## /config 命令

Claude Code 提供了交互式的配置界面：

```
$ /config

┌─ Settings ────────────────────────────────────┐
│                                                │
│  Model:       claude-sonnet-4-20250514   [Edit]│
│  Theme:       dark                       [Edit]│
│  Permissions: Default mode               [Edit]│
│                                                │
│  Permission Rules:                             │
│  ✅ Allow: Bash(git *), FileRead(*)            │
│  ❌ Deny:  Bash(rm -rf *)                      │
│  ❓ Ask:   Bash(git push *)                    │
│                                                │
│  MCP Servers:                                  │
│  🟢 github (connected)                         │
│  🔴 database (disconnected)                    │
│                                                │
│  [Save] [Cancel]                               │
└────────────────────────────────────────────────┘
```

这比手动编辑 JSON 文件方便得多——你不需要记住配置格式，也不容易写错。

## 本章小结

- 配置有严格的优先级：CLI > 环境变量 > 管理员策略 > 用户设置 > 默认值
- `settings.json` 包含模型、权限、MCP、Hook、主题、快捷键等配置
- 管理员策略（`managed-settings.json`）不能被用户覆盖
- 配置支持动态更新——修改后自动生效
- **GrowthBook** 功能开关支持渐进式发布和 A/B 测试
- 配置迁移确保版本升级时的兼容性

## 思考题

1. 为什么需要管理员策略？直接让用户自己配置不行吗？
2. 功能开关的"渐进式发布"有什么好处？为什么不直接发布给所有人？
3. 如果你要给 Claude Code 添加一个新的配置项，你需要考虑哪些事情？

## 配置设计的普遍原则

Claude Code 的配置系统体现了一些通用的配置设计原则：

### 1. 合理的默认值（Convention over Configuration）

大部分用户不需要修改任何配置就能正常使用。默认值是经过精心选择的——它们适合大多数场景。

### 2. 渐进式暴露（Progressive Disclosure）

新用户看到简单的配置界面。随着使用深入，他们会发现更多配置选项。不会一上来就用 50 个选项淹没用户。

### 3. 向后兼容（Backward Compatibility）

旧版本的配置文件在新版本中仍然能工作。配置迁移系统自动处理格式升级。用户不会因为升级软件而需要重写配置。

这三个原则不仅适用于 Claude Code，也适用于你将来开发的任何需要配置的软件。

下一章，我们将进入总结篇——回顾整个架构的美学。
