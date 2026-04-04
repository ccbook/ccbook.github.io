# 附录 B：源码中的关键文件索引

本附录列出了 Claude Code 源码中最重要的文件及其职责，方便你在阅读源码时快速定位。

## 入口与配置

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/main.tsx` | ~4,600 | 程序入口，三阶段启动 | 第 4 章 |
| `src/entrypoints/` | 多文件 | 不同启动模式（REPL/SDK/Bridge） | 第 4 章 |
| `src/constants/` | 多文件 | 全局常量定义 | - |

## 查询与对话

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/query.ts` | ~68,000 | 查询管道，消息流处理 | 第 8-9 章 |
| `src/QueryEngine.ts` | ~46,000 | API 调用和工具执行循环 | 第 9-10 章 |
| `src/history.ts` | - | 对话历史管理 | 第 8 章 |

## 工具系统

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/Tool.ts` | ~29,000 | 工具类型定义和 buildTool() | 第 12 章 |
| `src/tools.ts` | ~17,000 | 工具注册中心 | 第 12 章 |
| `src/tools/BashTool/` | 18+ 文件 | Bash 工具实现 | 第 13 章 |
| `src/tools/FileReadTool/` | - | 文件读取工具 | 第 14 章 |
| `src/tools/FileEditTool/` | - | 文件编辑工具 | 第 14 章 |
| `src/tools/FileWriteTool/` | - | 文件写入工具 | 第 14 章 |
| `src/tools/GlobTool/` | - | 文件名搜索工具 | 第 15 章 |
| `src/tools/GrepTool/` | - | 文件内容搜索工具 | 第 15 章 |
| `src/tools/AgentTool/` | 17 目录 | 子智能体工具 | 第 16 章 |
| `src/tools/WebFetchTool/` | - | 网页获取工具 | - |
| `src/tools/WebSearchTool/` | - | 网络搜索工具 | - |
| `src/tools/ToolSearchTool/` | - | 延迟加载工具发现 | 第 12 章 |

## 命令系统

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/commands.ts` | ~25,000 | 命令注册中心 | 第 7 章 |
| `src/commands/commit/` | - | /commit 命令 | 第 7 章 |
| `src/commands/compact/` | - | /compact 命令 | 第 7 章 |
| `src/commands/review/` | - | /review 命令 | - |
| `src/commands/context/` | - | /context 命令 | 第 11 章 |

## UI 组件

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/components/App.tsx` | - | 根组件 | 第 5 章 |
| `src/components/FullscreenLayout/` | - | 主界面布局 | 第 5 章 |
| `src/components/PermissionRequest/` | - | 权限请求对话框 | 第 17 章 |
| `src/components/FileEditToolDiff/` | - | 文件差异显示 | 第 5 章 |
| `src/screens/REPL.tsx` | ~2,000 | REPL 交互界面 | 第 5 章 |

## 权限与安全

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/hooks/useCanUseTool.tsx` | ~40,000 | 权限决策引擎 | 第 17 章 |
| Bash 安全相关（18 文件） | ~500,000 | 危险命令检测 | 第 18 章 |
| `src/types/permissions.ts` | - | 权限类型定义 | 第 17 章 |

## 状态管理

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/state/AppState.tsx` | - | 全局状态定义 | 第 6 章 |
| `src/state/AppStateStore.ts` | - | Zustand 状态仓库 | 第 6 章 |

## 服务层

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/services/api/claude.ts` | - | Claude API 调用 | 第 9 章 |
| `src/services/api/withRetry.ts` | - | 重试逻辑 | 第 9 章 |
| `src/services/mcp/` | 25 文件 | MCP 协议实现 | 第 20 章 |
| `src/services/compact/` | - | 对话压缩服务 | 第 11 章 |

## 扩展系统

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/bridge/` | 33 文件 | IDE 桥接系统 | 第 22 章 |
| `src/plugins/` | - | 插件系统 | 第 23 章 |
| `src/skills/` | - | 技能系统 | 第 23 章 |
| `src/coordinator/` | - | 多智能体协调 | 第 24 章 |

## 持久化

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/memdir/` | - | 记忆系统 | 第 26 章 |
| `src/utils/sessionStorage.ts` | - | 会话存储 | 第 26 章 |
| `src/migrations/` | - | 配置格式迁移 | 第 27 章 |

## 工具函数

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/utils/` | 331 文件 | 通用工具函数 | 全书 |
| `src/utils/settings/` | - | 配置管理 | 第 27 章 |
| `src/utils/tokens.ts` | - | Token 计数 | 第 11 章 |
| `src/utils/processUserInput/` | - | 用户输入处理 | 第 8 章 |

## React Hooks

| 文件 | 行数 | 职责 | 相关章节 |
|------|------|------|---------|
| `src/hooks/useCanUseTool.ts` | ~40,000 | 权限检查 Hook | 第 17 章 |
| `src/hooks/useArrowKeyHistory.ts` | - | 历史记录导航 | 第 5 章 |
| `src/hooks/useGlobalKeybindings.ts` | - | 全局快捷键 | 第 5 章 |
| `src/hooks/useSettingsChange.ts` | - | 配置文件监听 | 第 27 章 |
