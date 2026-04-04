# 第5章：终端里的 React——Ink 框架揭秘

## 终端也能有漂亮的界面？

当你打开 Claude Code，你会看到彩色的文字、整齐的布局、闪烁的光标、还有漂亮的代码高亮。这一切都在终端里完成——没有浏览器，没有图形窗口。

这是怎么做到的？答案是 **Ink**——一个让你用 React 在终端里构建界面的框架。

## 终端的"像素"

在浏览器里，最小的显示单位是像素（pixel）。一个 1920×1080 的屏幕有超过 200 万个像素。

在终端里，最小的显示单位是**字符**。一个典型的终端窗口大约是 80 列 × 24 行，也就是只有 1,920 个"像素"。

但终端字符不只有黑白两种。现代终端支持：

- **256 色**或**真彩色**（1600 万色）
- **粗体**、*斜体*、~~删除线~~、下划线
- **背景色**
- **特殊符号**：─ │ ┌ ┐ └ ┘ ├ ┤ （画框框用的）

这些效果通过一种叫做 **ANSI 转义码** 的特殊字符序列来实现：

```
\x1b[31m    ← 切换到红色
Hello       ← 这个文字会显示为红色
\x1b[0m     ← 恢复默认颜色
```

直接操作 ANSI 码很痛苦。Ink 把这些底层细节封装起来，让你用 React 的方式写界面。

## Ink 的核心组件

### Box——布局容器

`Box` 相当于网页里的 `<div>`，用来做布局：

```typescript
import { Box, Text } from "ink"

function Layout() {
  return (
    <Box flexDirection="column" padding={1}>
      <Box borderStyle="round" borderColor="cyan" paddingX={2}>
        <Text bold color="cyan">Claude Code v1.0</Text>
      </Box>
      <Box marginTop={1}>
        <Text>欢迎使用！请输入你的问题。</Text>
      </Box>
    </Box>
  )
}
```

在终端里会显示成这样：

```
 ╭──────────────────────╮
 │  Claude Code v1.0    │
 ╰──────────────────────╯

 欢迎使用！请输入你的问题。
```

`Box` 支持 flexbox 布局——和网页 CSS 的 flexbox 是一样的概念：

```typescript
// 水平排列
<Box flexDirection="row">
  <Text>左边</Text>
  <Text>右边</Text>
</Box>

// 垂直排列
<Box flexDirection="column">
  <Text>上面</Text>
  <Text>下面</Text>
</Box>

// 等分空间
<Box>
  <Box flexGrow={1}><Text>占 1/3</Text></Box>
  <Box flexGrow={2}><Text>占 2/3</Text></Box>
</Box>
```

### Text——文字显示

`Text` 相当于 `<span>`，用来显示文字：

```typescript
<Text color="green" bold>成功！</Text>
<Text color="red" italic>错误：文件不存在</Text>
<Text dimColor>（这段文字颜色较暗）</Text>
<Text underline>这段文字有下划线</Text>
```

### TextInput——用户输入

```typescript
function InputDemo() {
  const [value, setValue] = useState("")

  return (
    <Box>
      <Text bold>{">"} </Text>
      <TextInput
        value={value}
        onChange={setValue}
        onSubmit={(text) => {
          console.log("用户输入了:", text)
        }}
      />
    </Box>
  )
}
```

这会在终端里显示一个 `>` 提示符，后面跟着一个可以打字的输入区域。

## Claude Code 的界面结构

让我们看看 Claude Code 的主界面是怎么组成的：

```
┌─────────────────────────────────────────────────────┐
│  Claude Code  v1.0.0        model: opus    cost: $0 │  ← 状态栏
├─────────────────────────────────────────────────────┤
│                                                      │
│  User: 帮我看看这个文件                               │  ← 消息区域
│                                                      │
│  Claude: 让我读取这个文件。                            │
│  📄 Read index.ts                                    │
│  文件内容如下：                                       │
│  ...                                                 │
│                                                      │
├─────────────────────────────────────────────────────┤
│  > 你的输入在这里...                                  │  ← 输入框
└─────────────────────────────────────────────────────┘
```

对应的组件层次大致是：

```typescript
<App>
  <FullscreenLayout>
    <StatusBar />          {/* 顶部状态栏 */}
    <MessageArea>          {/* 中间消息区域 */}
      <Message role="user" />
      <Message role="assistant">
        <ToolUseDisplay />  {/* 工具使用的显示 */}
        <TextContent />     {/* 文字内容 */}
      </Message>
    </MessageArea>
    <InputBox />           {/* 底部输入框 */}
  </FullscreenLayout>
</App>
```

## 146 个组件——终端里的 UI 库

Claude Code 有 146 个 React 组件。让我们看看一些有趣的：

### PermissionRequest——权限对话框

当 AI 想执行一个需要确认的操作时，会弹出一个权限对话框：

```
┌─ Permission Request ─────────────────────────────┐
│                                                    │
│  Claude wants to run:                              │
│  $ git push origin main                            │
│                                                    │
│  [Allow]  [Deny]  [Allow Always]                   │
│                                                    │
└────────────────────────────────────────────────────┘
```

这个对话框就是一个 React 组件。它接收"要显示什么操作"作为属性，然后渲染出漂亮的对话框。

### FileEditToolDiff——代码差异显示

当 AI 修改了文件，它会显示修改前后的差异：

```
  index.ts
  ────────
  - const result = data.value    ← 删除的行（红色）
  + const result = data.value ?? 0  ← 新增的行（绿色）
```

这不是简单的文字——它需要：
1. 计算修改前后的差异（diff 算法）
2. 对代码做语法高亮
3. 用红绿颜色标记增删

### Spinner——加载动画

当 AI 正在思考时，你会看到一个转动的加载动画：

```
⠋ Thinking... (1,234 tokens)
⠙ Thinking... (2,456 tokens)
⠹ Thinking... (3,789 tokens)
```

这些 `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` 是 Unicode 的盲文字符（Braille characters），快速切换显示就产生了"旋转"的效果。

## 渲染原理

Ink 的渲染过程和浏览器里的 React 类似：

```
1. 构建虚拟 DOM（Virtual DOM）
   React 组件 → JavaScript 对象树

2. 比较差异（Diffing）
   新的对象树 vs 旧的对象树 → 找出变化

3. 应用更新（Patching）
   只更新变化的部分 → 输出 ANSI 转义码到终端
```

为什么不每次都重新画整个屏幕？因为终端的"刷新"比浏览器慢得多。如果每次都全部重画，你会看到明显的闪烁。通过只更新变化的部分（diff 算法），界面显示得很流畅。

## 主题系统

Claude Code 支持多种主题——你可以用 `/theme` 命令切换：

```typescript
// 简化的主题定义
const darkTheme = {
  primary: "cyan",
  success: "green",
  error: "red",
  warning: "yellow",
  text: "white",
  dimText: "gray",
  border: "gray",
}

const lightTheme = {
  primary: "blue",
  success: "green",
  error: "red",
  warning: "orange",
  text: "black",
  dimText: "darkGray",
  border: "lightGray",
}
```

组件通过读取当前主题来决定颜色：

```typescript
function SuccessMessage({ text }: { text: string }) {
  const theme = useTheme()  // 获取当前主题
  return <Text color={theme.success}>{text}</Text>
}
```

这样只需要改主题配置，所有组件的颜色就会一起变。这就是"关注点分离"的好处——颜色的定义和颜色的使用分开了。

## 响应式布局

终端窗口的大小是可变的。Claude Code 需要适应不同的窗口大小：

```typescript
function ResponsiveLayout() {
  // 获取当前终端尺寸
  const { columns, rows } = useTerminalSize()

  if (columns < 60) {
    // 窄屏：简化布局
    return <CompactLayout />
  } else {
    // 宽屏：完整布局
    return <FullLayout />
  }
}
```

当你拖动终端窗口改变大小时，Ink 会自动重新渲染界面，就像浏览器里的响应式网页一样。

## 键盘事件

在终端里，没有鼠标（大多数情况下）。所有交互都通过键盘：

```typescript
import { useInput } from "ink"

function MyComponent() {
  useInput((input, key) => {
    if (key.ctrl && input === "c") {
      // Ctrl+C：退出
      process.exit(0)
    }
    if (key.upArrow) {
      // 上箭头：显示上一条消息
      showPreviousMessage()
    }
    if (key.tab) {
      // Tab：自动补全
      autoComplete()
    }
  })

  return <Text>按 Ctrl+C 退出</Text>
}
```

Claude Code 有一个完整的快捷键系统（`keybindings/` 目录），用户可以自定义按键绑定。

## 为什么选择 React + Ink？

你可能会问：为什么要用 React 来写终端界面？直接用 `console.log` 不行吗？

对于简单的程序，`console.log` 当然够用。但 Claude Code 的界面很复杂：
- 消息会不断增加（滚动）
- AI 回复是逐字出现的（流式更新）
- 权限对话框需要覆盖在消息上面（层叠）
- 工具执行的进度需要实时更新
- 用户随时可能调整窗口大小

用 `console.log` 管理这些状态会变成一场噩梦。React 的"声明式"模式——你描述界面**应该是什么样**，React 负责**怎么让它变成那样**——极大地简化了这个问题。

打个比方：`console.log` 就像你拿着画笔一笔一笔在画布上画画，每次要改一个地方都得把整幅画重画一遍。React 就像你告诉一个画家"我要一幅有山有水的画"，画家帮你画好，下次你说"把山改成蓝色"，画家只改山的颜色，其他不动。

## 本章小结

- **Ink** 让 React 在终端里工作，用 `Box`、`Text`、`TextInput` 替代 HTML 元素
- 终端的"像素"是字符，通过 ANSI 转义码实现颜色和样式
- Claude Code 有 146 个组件，构成了完整的终端 UI
- Ink 使用虚拟 DOM 和 diff 算法，只更新变化的部分
- 主题系统、响应式布局、键盘事件都通过 React 的方式实现
- 选择 React + Ink 是因为界面状态复杂，声明式编程更容易管理

## 动手练习

1. 试着在纸上画出 Claude Code 的界面，标注每个区域对应哪个组件
2. 如果你要实现一个加载动画，你会怎么用 React 来写？（提示：用 `useState` 存储当前帧，用 `useEffect` 设置定时器）
3. 想想看：如果不用 React，用纯 `console.log` 实现流式显示（逐字出现的效果），你会怎么做？

## 一个有趣的事实

你知道吗？Ink 框架的名字来自"墨水"——因为终端的输出就像用墨水在纸上写字一样，一旦"打印"出来就很难修改。

但 Ink 用了一个巧妙的技巧来实现"修改已打印内容"的效果：它使用 ANSI 转义码中的**光标移动**指令，把光标移回之前的位置，然后覆盖旧内容。

```
第一帧：
  ⠋ Loading... (0s)
                     ← 光标在这里

第二帧（光标移回行首，覆盖）：
  ⠙ Loading... (1s)
                     ← 覆盖了旧内容
```

这就是为什么你看到加载动画在"旋转"——其实是不断覆盖同一行的内容。

电影也是一样的原理：快速连续播放静止画面，就产生了运动的错觉。终端动画的帧率通常是 12-30 FPS（每秒 12-30 帧），足以让人眼觉得是流畅的动画。

下一章，我们将学习程序的"记忆"——状态管理。
