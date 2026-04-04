<div align="center">

<!-- 等待替换为实际封面图 -->
<!-- <img src="cover.png" width="400" /> -->

# 解密 Claude Code

### 一个 AI 编程助手的源码之旅

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Chapters](https://img.shields.io/badge/chapters-30-blue)]()
[![Target](https://img.shields.io/badge/target-高中生-orange)]()

> *"最好的学习方式不是被告知答案，而是亲眼看到答案是怎么被构建出来的。"*

**30 章正文 · 3 个附录 · 150+ 代码示例 · 40+ 架构图**

[开始阅读](#目录) · [在线预览](#快速开始) · [参与贡献](#贡献指南)

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

## 适合谁读

- **会初级编程的高中生** —— 知道变量、函数、循环就够了
- **想了解大型项目的初学者** —— 从课堂小程序到 50 万行的跨越
- **对 AI 工具感兴趣的开发者** —— 理解 AI Agent 的完整实现

不需要你会 TypeScript 或 React，第 3 章会从零讲起。

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/nicekid1/Demystifying-Claude-Code.git
cd Demystifying-Claude-Code

# 在浏览器中阅读（默认）
make

# 或启动本地预览服务器
make serve

# 生成 PDF
make pdf

# 生成 EPUB
make epub
```

### 构建依赖

| 格式 | 依赖 | 安装方式 |
|------|------|---------|
| HTML（浏览器阅读） | Python 3 | macOS 自带 |
| PDF | pandoc + LaTeX | `brew install pandoc && brew install --cask mactex-no-gui` |
| PDF（备选） | pandoc + weasyprint | `brew install pandoc && pip3 install weasyprint` |
| EPUB | pandoc | `brew install pandoc` |

## 目录

### 第一部分：起步篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 1 章](chapter01.md) | 欢迎来到 Claude Code 的世界 | 全书导览、为什么读源码 |
| [第 2 章](chapter02.md) | 源码全景地图 | 目录结构、分层架构、数据流 |
| [第 3 章](chapter03.md) | 从零理解 TypeScript 与 React | TS 速成、React/Ink/Zod/Zustand |

### 第二部分：核心架构篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 4 章](chapter04.md) | 程序的大门——入口文件解析 | 三阶段启动、功能开关、五种模式 |
| [第 5 章](chapter05.md) | 终端里的 React——Ink 框架揭秘 | ANSI 转义码、Box/Text、虚拟 DOM |
| [第 6 章](chapter06.md) | 状态管理——程序的"记忆" | Zustand、选择器、不可变更新 |
| [第 7 章](chapter07.md) | 命令系统——斜杠的魔法 | 50+ 命令、/compact、命令面板 |

### 第三部分：对话引擎篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 8 章](chapter08.md) | 与 AI 对话的秘密——消息系统 | 消息类型、处理流水线、系统提示词 |
| [第 9 章](chapter09.md) | 查询引擎——大脑中枢 | Agent Loop、API 调用、工具串行/并行 |
| [第 10 章](chapter10.md) | 流式响应——逐字显示的魔法 | SSE、事件处理、中断策略 |
| [第 11 章](chapter11.md) | 上下文管理——有限的记忆 | Token 预算、提示缓存、自动压缩 |

### 第四部分：工具系统篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 12 章](chapter12.md) | 工具的世界——从设计到实现 | 统一接口、故障安全、延迟加载 |
| [第 13 章](chapter13.md) | Bash 工具——最强大也最危险 | 危险命令检测、权限规则、沙箱 |
| [第 14 章](chapter14.md) | 文件三剑客——Read、Write、Edit | 大文件处理、先读后写、差异显示 |
| [第 15 章](chapter15.md) | 搜索双雄——Grep 与 Glob | ripgrep、正则表达式、搜索策略 |
| [第 16 章](chapter16.md) | Agent 工具——AI 的分身术 | 子智能体、并行执行、worktree 隔离 |

### 第五部分：安全与权限篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 17 章](chapter17.md) | 权限系统——信任的层级 | 三种模式、六步检查、权限对话框 |
| [第 18 章](chapter18.md) | 安全防线——危险命令检测 | 命令语义分析、路径验证、AI 分类器 |
| [第 19 章](chapter19.md) | 沙箱机制——隔离的艺术 | 最小权限、纵深防御、安全设计哲学 |

### 第六部分：扩展与集成篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 20 章](chapter20.md) | MCP 协议——工具的万能接口 | Stdio/SSE/WebSocket、工具发现 |
| [第 21 章](chapter21.md) | Hook 系统——可编程的钩子 | PreToolUse、PostToolUse、开放封闭原则 |
| [第 22 章](chapter22.md) | IDE 桥接——编辑器中的 AI | WebSocket、JWT 认证、前后端分离 |
| [第 23 章](chapter23.md) | 插件与技能——无限扩展 | 技能文件、插件系统、扩展生态 |

### 第七部分：高级话题篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 24 章](chapter24.md) | 多智能体——AI 的团队协作 | 协调者模式、团队智能体、后台运行 |
| [第 25 章](chapter25.md) | 性能优化——毫秒必争 | 并行预加载、LRU 缓存、推测性执行 |
| [第 26 章](chapter26.md) | 持久化记忆——跨会话的智慧 | CLAUDE.md、会话记录、自动提取 |
| [第 27 章](chapter27.md) | 配置系统——千人千面 | 配置层次、管理员策略、GrowthBook |

### 第八部分：总结篇

| 章节 | 主题 | 关键词 |
|------|------|--------|
| [第 28 章](chapter28.md) | 架构之美——设计模式总结 | 十大设计模式、模式组合 |
| [第 29 章](chapter29.md) | 从源码到产品——工程实践启示 | 十大工程实践 |
| [第 30 章](chapter30.md) | 你的下一步——成为更好的程序员 | 学习路线、推荐资源 |

### 附录

| 文件 | 内容 |
|------|------|
| [附录 A](appendix-a.md) | 术语表（50+ 术语） |
| [附录 B](appendix-b.md) | 源码关键文件索引 |
| [附录 C](appendix-c.md) | 全书知识地图（架构图、依赖图、速查表） |

## 数字一览

| | Claude Code 源码 | 本书 |
|---|---|---|
| 文件数 | ~1,884 个 TypeScript 文件 | 36 个 Markdown 文件 |
| 总行数 | ~512,000 行 | ~9,300 行 |
| 工具/章节 | 40+ 内置工具 | 30 章 + 3 附录 |
| 组件/图表 | 146 个 React 组件 | 40+ ASCII 架构图 |
| Hooks/示例 | 87 个 React Hooks | 150+ 代码示例 |

## 项目结构

```
.
├── README.md           ← 你在这里
├── Makefile            ← 构建入口
├── build.sh            ← 构建脚本
├── cover.md            ← 封面页
├── cover.png           ← 封面图片（待添加）
├── preface.md          ← 前言
├── chapter01.md        ← 第 1 章
├── ...
├── chapter30.md        ← 第 30 章
├── appendix-a.md       ← 术语表
├── appendix-b.md       ← 文件索引
├── appendix-c.md       ← 知识地图
├── about-author.md     ← 关于本书
└── build/              ← 构建产物（git ignored）
```

## 贡献指南

欢迎任何形式的贡献！

### 你可以做什么

- **纠错** —— 发现错别字、代码错误、事实偏差？提个 Issue 或 PR
- **改进** —— 觉得某个解释不够清楚？某个比喻可以更好？欢迎优化
- **翻译** —— 想把某些章节翻译成英文或其他语言？非常欢迎
- **补充** —— 想加一个新的"动手练习"或"思考题"？提 PR 吧

### 贡献流程

```bash
# 1. Fork 并克隆
git clone https://github.com/你的用户名/Demystifying-Claude-Code.git

# 2. 创建分支
git checkout -b fix/chapter3-typo

# 3. 修改并提交
git add .
git commit -m "修复第3章的代码示例错误"

# 4. 推送并创建 PR
git push origin fix/chapter3-typo
```

### 写作风格指南

- **读者是高中生** —— 不要假设读者有工程经验，解释每个专业术语
- **多用比喻** —— 用日常生活的例子来解释抽象概念
- **代码要简化** —— 只保留核心逻辑，去掉错误处理和类型噪音
- **每章独立** —— 每章应该可以独立阅读（必要时注明"参见第 X 章"）

## 致谢

- [Anthropic](https://www.anthropic.com/) —— Claude Code 的开发者
- 所有为开源社区贡献代码和文档的人

## 许可证

本书以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可证开源。

你可以自由地：
- **分享** —— 以任何媒介或格式复制、转载本书
- **演绎** —— 重混、转换、基于本书创作

但需要遵守：
- **署名** —— 标明原作者和出处
- **非商业性** —— 不得用于商业目的
- **相同方式共享** —— 衍生作品必须以相同许可证发布

---

<div align="center">

**如果这本书对你有帮助，请给个 Star 支持一下**

</div>
