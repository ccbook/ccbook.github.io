#!/usr/bin/env bash
set -euo pipefail

# 《解密 Claude Code》书籍构建脚本
# 用法: ./build.sh [web|pdf|epub]

BOOK_TITLE="解密 Claude Code：一个 AI 编程助手的源码之旅"
OUTPUT_DIR="build"
PORT=8000

# 按阅读顺序排列的章节文件
CHAPTERS=(
  cover.md
  preface.md
  chapter01.md chapter02.md chapter03.md
  chapter04.md chapter05.md chapter06.md chapter07.md
  chapter08.md chapter09.md chapter10.md chapter11.md
  chapter12.md chapter13.md chapter14.md chapter15.md chapter16.md
  chapter17.md chapter18.md chapter19.md
  chapter20.md chapter21.md chapter22.md chapter23.md
  chapter24.md chapter25.md chapter26.md chapter27.md
  chapter28.md chapter29.md chapter30.md
  appendix-a.md appendix-b.md appendix-c.md
  about-author.md
)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# 检查依赖
check_dep() {
  if ! command -v "$1" &>/dev/null; then
    error "$1 未安装。$2"
    return 1
  fi
}

# 合并所有章节为一个 Markdown 文件
merge_chapters() {
  local output="$1"
  mkdir -p "$OUTPUT_DIR"
  > "$output"
  for ch in "${CHAPTERS[@]}"; do
    if [[ -f "$ch" ]]; then
      cat "$ch" >> "$output"
      echo -e "\n\n---\n\n" >> "$output"
    else
      warn "文件不存在，跳过: $ch"
    fi
  done
  # 复制图片资源到输出目录
  for img in cover.jpg wx.png; do
    [[ -f "$img" ]] && cp -f "$img" "$OUTPUT_DIR/"
  done
  info "已合并 ${#CHAPTERS[@]} 个文件 → $output"
}

# 构建 HTML（左右双栏布局，用于 Web 预览）
build_html() {
  mkdir -p "$OUTPUT_DIR"
  info "构建双栏 HTML..."
  python3 "$(dirname "$0")/scripts/build_html.py" "." "$OUTPUT_DIR"
  info "HTML 已生成 → $OUTPUT_DIR/index.html"
}

# 构建 PDF
build_pdf() {
  check_dep pandoc "请安装: brew install pandoc" || return 1

  local merged="$OUTPUT_DIR/book.md"
  local pdf="$OUTPUT_DIR/解密ClaudeCode.pdf"
  merge_chapters "$merged"

  # 检查是否有中文 PDF 引擎
  local pdf_engine=""
  if command -v xelatex &>/dev/null; then
    pdf_engine="--pdf-engine=xelatex"
  elif command -v lualatex &>/dev/null; then
    pdf_engine="--pdf-engine=lualatex"
  elif command -v weasyprint &>/dev/null; then
    # 用 weasyprint 作为备选（Markdown→HTML→PDF）
    info "使用 weasyprint 生成 PDF..."
    local html_single="$OUTPUT_DIR/book_single.html"

    # 先生成不带封面的合并文件（跳过 cover.md）
    local merged_no_cover="$OUTPUT_DIR/book_no_cover.md"
    > "$merged_no_cover"
    for ch in "${CHAPTERS[@]}"; do
      [[ "$ch" == "cover.md" ]] && continue
      if [[ -f "$ch" ]]; then
        cat "$ch" >> "$merged_no_cover"
        echo -e "\n\n---\n\n" >> "$merged_no_cover"
      fi
    done

    pandoc "$merged_no_cover" \
      --from markdown \
      --to html5 \
      --standalone \
      --toc \
      --toc-depth=2 \
      --metadata title="$BOOK_TITLE" \
      --highlight-style=tango \
      -V lang=zh-CN \
      -o "$html_single"

    # 在 <body> 后插入封面图作为第一页
    python3 -c "
import sys
html = open(sys.argv[1], encoding='utf-8').read()
cover = '''<div style=\"text-align:center;page-break-after:always;padding-top:100px;\">
<img src=\"cover.jpg\" style=\"max-width:500px;\" />
<h1 style=\"margin-top:1em;\">$BOOK_TITLE</h1>
<p style=\"color:#666;\">everettjf | Claude Code</p>
</div>'''
html = html.replace('<body>', '<body>' + cover, 1)
open(sys.argv[1], 'w', encoding='utf-8').write(html)
" "$html_single"

    # 注入中文字体样式
    python3 -c "
import sys
html = open(sys.argv[1], encoding='utf-8').read()
css = '<style>body, p, h1, h2, h3, h4, h5, h6, li, td, th, span, div { font-family: \"Hiragino Sans GB\", \"Heiti SC\", \"STSong\", \"Arial Unicode MS\", sans-serif; } code, pre { font-family: Menlo, \"Hiragino Sans GB\", monospace; }</style>'
html = html.replace('</head>', css + '</head>', 1)
open(sys.argv[1], 'w', encoding='utf-8').write(html)
" "$html_single"

    weasyprint "$html_single" "$pdf"
    info "PDF 已生成 → $pdf"
    return 0
  else
    warn "未找到 xelatex/lualatex/weasyprint。尝试基础 pandoc..."
    pdf_engine=""
  fi

  pandoc "$merged" \
    --from markdown \
    --to pdf \
    $pdf_engine \
    --toc \
    --toc-depth=2 \
    --metadata title="$BOOK_TITLE" \
    --highlight-style=tango \
    -V geometry:margin=2.5cm \
    -V fontsize=11pt \
    -V documentclass=report \
    -V CJKmainfont="PingFang SC" \
    -V mainfont="PingFang SC" \
    -V monofont="Menlo" \
    -V linkcolor=cyan \
    -o "$pdf" 2>/dev/null || {
      warn "LaTeX PDF 生成失败，尝试 HTML→PDF 备选方案..."
      if command -v weasyprint &>/dev/null; then
        local html_single="$OUTPUT_DIR/book_single.html"
        pandoc "$merged" \
          --from markdown \
          --to html5 \
          --standalone \
          --toc \
          --toc-depth=2 \
          --metadata title="$BOOK_TITLE" \
          --highlight-style=tango \
          -V lang=zh-CN \
          -o "$html_single"
        # 注入中文字体样式
        python3 -c "
import sys
html = open(sys.argv[1], encoding='utf-8').read()
css = '<style>body, p, h1, h2, h3, h4, h5, h6, li, td, th, span, div { font-family: \"Hiragino Sans GB\", \"Heiti SC\", \"STSong\", \"Arial Unicode MS\", sans-serif; } code, pre { font-family: Menlo, \"Hiragino Sans GB\", monospace; }</style>'
html = html.replace('</head>', css + '</head>', 1)
open(sys.argv[1], 'w', encoding='utf-8').write(html)
" "$html_single"
        weasyprint "$html_single" "$pdf"
      else
        error "PDF 生成失败。请安装以下任一工具："
        error "  brew install --cask mactex-no-gui  # LaTeX (推荐)"
        error "  pip3 install weasyprint             # weasyprint"
        return 1
      fi
    }

  info "PDF 已生成 → $pdf"
}

# 构建 EPUB
build_epub() {
  check_dep pandoc "请安装: brew install pandoc" || return 1

  local merged="$OUTPUT_DIR/book.md"
  local epub="$OUTPUT_DIR/解密ClaudeCode.epub"
  merge_chapters "$merged"

  local cover_opt=""
  if [[ -f "cover.jpg" ]]; then
    cover_opt="--epub-cover-image=cover.jpg"
  fi

  pandoc "$merged" \
    --from markdown \
    --to epub3 \
    --toc \
    --toc-depth=2 \
    --metadata title="$BOOK_TITLE" \
    --metadata language="zh-CN" \
    --highlight-style=tango \
    --resource-path=".:$OUTPUT_DIR" \
    $cover_opt \
    -o "$epub"

  info "EPUB 已生成 → $epub"
}

# 启动 Web 服务器预览
serve_web() {
  build_html
  info "启动 Web 预览服务器 → http://localhost:$PORT"
  info "按 Ctrl+C 停止"
  cd "$OUTPUT_DIR"
  if command -v python3 &>/dev/null; then
    python3 -m http.server "$PORT"
  elif command -v python &>/dev/null; then
    python -m SimpleHTTPServer "$PORT"
  else
    error "需要 python3 来启动 Web 服务器"
    info "你也可以直接在浏览器中打开 $OUTPUT_DIR/index.html"
    return 1
  fi
}

# 清理构建产物
clean() {
  rm -rf "$OUTPUT_DIR"
  info "已清理 $OUTPUT_DIR/"
}

# 主入口
case "${1:-web}" in
  web)   serve_web ;;
  html)  build_html ;;
  pdf)   build_pdf ;;
  epub)  build_epub ;;
  clean) clean ;;
  all)
    build_html
    build_pdf
    build_epub
    info "全部构建完成！输出目录: $OUTPUT_DIR/"
    ;;
  *)
    echo "用法: $0 [web|html|pdf|epub|clean|all]"
    echo ""
    echo "  web    构建 HTML 并启动本地预览服务器（默认）"
    echo "  html   仅构建 HTML"
    echo "  pdf    构建 PDF（需要 pandoc + LaTeX 或 weasyprint）"
    echo "  epub   构建 EPUB（需要 pandoc）"
    echo "  clean  清理构建产物"
    echo "  all    构建所有格式"
    exit 1
    ;;
esac
