<div align="center">

<img src="cover.jpg" width="400" />

# 解密 Claude Code

### 一个 AI 编程助手的源码之旅

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Chapters](https://img.shields.io/badge/chapters-30-blue)]()

> *"最好的学习方式不是被告知答案，而是亲眼看到答案是怎么被构建出来的。"*

**30 章正文 · 3 个附录 · 150+ 代码示例 · 40+ 架构图**

**作者：everettjf** · 使用 Claude Code 分析泄露源码 · 保留出处即可自由转载

[**在线阅读**](https://ccbook.github.io) · [**下载 PDF**](https://github.com/ccbook/ccbook.github.io/releases/latest) · [**下载 EPUB**](https://github.com/ccbook/ccbook.github.io/releases/latest)

</div>

---

## 这本书讲什么

Claude Code 是 Anthropic 开发的 AI 编程助手——一个运行在终端里、能读写文件、执行命令、甚至创建子智能体的 CLI 工具。它有约 **50 万行 TypeScript 代码**，分布在 **1,884 个文件**中。

这本书带你深入这份源码，看清一个真实的、被数百万人使用的 AI 产品是怎么从零构建的。

你会学到：

- **AI Agent 是怎么工作的** —— 思考→行动→观察的核心循环
- **工具系统怎么设计** —— 40+ 工具的统一接口与调度机制
- **安全系统怎么搭建** —— 六层纵深防御，50 万行安全代码
- **大型项目怎么组织** —— 分层架构、状态管理、模块化设计
- **十大设计模式** —— 从源码中提炼的可迁移的架构智慧

## 目录

### 第一部分：起步篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 1 章 | 欢迎来到 Claude Code 的世界 | 全书导览、为什么读源码 |
| 第 2 章 | 源码全景地图 | 目录结构、分层架构、数据流 |
| 第 3 章 | 从零理解 TypeScript 与 React | TS 速成、React/Ink/Zod/Zustand |

### 第二部分：核心架构篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 4 章 | 程序的大门——入口文件解析 | 三阶段启动、功能开关、五种模式 |
| 第 5 章 | 终端里的 React——Ink 框架揭秘 | ANSI 转义码、Box/Text、虚拟 DOM |
| 第 6 章 | 状态管理——程序的"记忆" | Zustand、选择器、不可变更新 |
| 第 7 章 | 命令系统——斜杠的魔法 | 50+ 命令、/compact、命令面板 |

### 第三部分：对话引擎篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 8 章 | 与 AI 对话的秘密——消息系统 | 消息类型、处理流水线、系统提示词 |
| 第 9 章 | 查询引擎——大脑中枢 | Agent Loop、API 调用、工具串行/并行 |
| 第 10 章 | 流式响应——逐字显示的魔法 | SSE、事件处理、中断策略 |
| 第 11 章 | 上下文管理——有限的记忆 | Token 预算、提示缓存、自动压缩 |

### 第四部分：工具系统篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 12 章 | 工具的世界——从设计到实现 | 统一接口、故障安全、延迟加载 |
| 第 13 章 | Bash 工具——最强大也最危险 | 危险命令检测、权限规则、沙箱 |
| 第 14 章 | 文件三剑客——Read、Write、Edit | 大文件处理、先读后写、差异显示 |
| 第 15 章 | 搜索双雄——Grep 与 Glob | ripgrep、正则表达式、搜索策略 |
| 第 16 章 | Agent 工具——AI 的分身术 | 子智能体、并行执行、worktree 隔离 |

### 第五部分：安全与权限篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 17 章 | 权限系统——信任的层级 | 三种模式、六步检查、权限对话框 |
| 第 18 章 | 安全防线——危险命令检测 | 命令语义分析、路径验证、AI 分类器 |
| 第 19 章 | 沙箱机制——隔离的艺术 | 最小权限、纵深防御、安全设计哲学 |

### 第六部分：扩展与集成篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 20 章 | MCP 协议——工具的万能接口 | Stdio/SSE/WebSocket、工具发现 |
| 第 21 章 | Hook 系统——可编程的钩子 | PreToolUse、PostToolUse、开放封闭原则 |
| 第 22 章 | IDE 桥接——编辑器中的 AI | WebSocket、JWT 认证、前后端分离 |
| 第 23 章 | 插件与技能——无限扩展 | 技能文件、插件系统、扩展生态 |

### 第七部分：高级话题篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 24 章 | 多智能体——AI 的团队协作 | 协调者模式、团队智能体、后台运行 |
| 第 25 章 | 性能优化——毫秒必争 | 并行预加载、LRU 缓存、推测性执行 |
| 第 26 章 | 持久化记忆——跨会话的智慧 | CLAUDE.md、会话记录、自动提取 |
| 第 27 章 | 配置系统——千人千面 | 配置层次、管理员策略、GrowthBook |

### 第八部分：总结篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| 第 28 章 | 架构之美——设计模式总结 | 十大设计模式、模式组合 |
| 第 29 章 | 从源码到产品——工程实践启示 | 十大工程实践 |
| 第 30 章 | 你的下一步——成为更好的程序员 | 学习路线、推荐资源 |

### 附录

| 文件 | 内容 |
|------|------|
| 附录 A | 术语表（50+ 术语） |
| 附录 B | 源码关键文件索引 |
| 附录 C | 全书知识地图（架构图、依赖图、速查表） |

## 本地构建

```bash
# 克隆仓库
git clone https://github.com/ccbook/ccbook.github.io.git
cd ccbook.github.io

# 在浏览器中阅读
make

# 生成 PDF
make pdf

# 生成 EPUB
make epub

# 一键部署（构建 + GitHub Pages + Release）
./deploy.sh
```

### 构建依赖

| 格式 | 依赖 | 安装方式 |
|------|------|---------|
| HTML | Python 3 | macOS 自带 |
| PDF | pandoc + weasyprint | `brew install pandoc && pip3 install weasyprint` |
| EPUB | pandoc | `brew install pandoc` |

## 贡献指南

欢迎任何形式的贡献！

- **纠错** —— 发现错别字、代码错误、事实偏差？提个 Issue 或 PR
- **改进** —— 觉得某个解释不够清楚？某个比喻可以更好？欢迎优化
- **翻译** —— 想把某些章节翻译成英文或其他语言？非常欢迎
- **补充** —— 想加一个新的"动手练习"或"思考题"？提 PR 吧

## 许可证

本书以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可证开源。保留出处即可自由转载。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ccbook/ccbook.github.io&type=Date)](https://star-history.com/#ccbook/ccbook.github.io&Date)

---

<div align="center">

**如果这本书对你有帮助，请给个 Star 支持一下**

</div>
