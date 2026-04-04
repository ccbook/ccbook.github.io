# 《解密 Claude Code》书籍构建
# ================================
#
# make          — 构建 HTML 并在浏览器中打开
# make pdf      — 构建 PDF
# make epub     — 构建 EPUB
# make all      — 构建所有格式
# make serve    — 启动本地预览服务器
# make clean    — 清理构建产物

.PHONY: web pdf epub all serve clean help

# 默认目标：构建 HTML 并打开浏览器
web: html open

html:
	@./build.sh html

open: html
	@echo "[INFO] 在浏览器中打开..."
	@if command -v open >/dev/null 2>&1; then \
		open build/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open build/index.html; \
	elif command -v start >/dev/null 2>&1; then \
		start build/index.html; \
	else \
		echo "[INFO] 请手动打开 build/index.html"; \
	fi

pdf:
	@./build.sh pdf

epub:
	@./build.sh epub

all:
	@./build.sh all

serve:
	@./build.sh web

clean:
	@./build.sh clean

help:
	@echo ""
	@echo "  《解密 Claude Code》构建系统"
	@echo "  =========================="
	@echo ""
	@echo "  make          构建 HTML 并在浏览器中打开（默认）"
	@echo "  make pdf      构建 PDF（需要 pandoc + LaTeX 或 weasyprint）"
	@echo "  make epub     构建 EPUB（需要 pandoc）"
	@echo "  make all      构建所有格式"
	@echo "  make serve    启动本地 Web 预览服务器（localhost:8000）"
	@echo "  make clean    清理构建产物"
	@echo "  make help     显示此帮助"
	@echo ""
	@echo "  依赖安装："
	@echo "    brew install pandoc                  # Markdown 转换"
	@echo "    brew install --cask mactex-no-gui    # PDF (LaTeX)"
	@echo "    pip3 install weasyprint              # PDF (备选)"
	@echo ""
	@echo "  输出目录: build/"
	@echo ""
