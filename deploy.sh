#!/usr/bin/env bash
set -euo pipefail

# 《解密 Claude Code》一键部署脚本
# 用法: ./deploy.sh
#
# 功能:
#   1. 构建 HTML / PDF / EPUB
#   2. 部署 HTML 到 GitHub Pages (gh-pages 分支)
#   3. 创建 GitHub Release，上传 PDF 和 EPUB
#   4. 自动递增版本号

VERSION_FILE=".version"
REPO="ccbook/ccbook.github.io"
OUTPUT_DIR="build"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 检查依赖 ──────────────────────────────────────────────────
command -v gh    &>/dev/null || error "需要 gh CLI: brew install gh"
command -v git   &>/dev/null || error "需要 git"
command -v pandoc &>/dev/null || error "需要 pandoc: brew install pandoc"

# ── 版本号管理 ────────────────────────────────────────────────
get_version() {
  if [[ -f "$VERSION_FILE" ]]; then
    cat "$VERSION_FILE"
  else
    echo "1.0"
  fi
}

bump_version() {
  local v="$1"
  local major minor
  major="${v%%.*}"
  minor="${v#*.}"
  minor=$((minor + 1))
  echo "${major}.${minor}"
}

VERSION=$(get_version)
NEW_VERSION=$(bump_version "$VERSION")
TAG="v${NEW_VERSION}"

info "当前版本: v${VERSION} → 新版本: ${TAG}"

# ── 构建 ──────────────────────────────────────────────────────
info "构建 HTML..."
./build.sh html

info "构建 PDF..."
./build.sh pdf

info "构建 EPUB..."
./build.sh epub

PDF_FILE="${OUTPUT_DIR}/解密ClaudeCode.pdf"
EPUB_FILE="${OUTPUT_DIR}/解密ClaudeCode.epub"

[[ -f "$PDF_FILE" ]]  || error "PDF 未生成: $PDF_FILE"
[[ -f "$EPUB_FILE" ]] || error "EPUB 未生成: $EPUB_FILE"

info "构建完成！PDF=$(du -h "$PDF_FILE" | cut -f1), EPUB=$(du -h "$EPUB_FILE" | cut -f1)"

# ── 更新落地页中的下载链接 ────────────────────────────────────
RELEASE_URL="https://github.com/${REPO}/releases/download/${TAG}"
for f in "${OUTPUT_DIR}"/*.html; do
  sed -i '' "s|{{pdf_url}}|${RELEASE_URL}/解密ClaudeCode.pdf|g" "$f"
  sed -i '' "s|{{epub_url}}|${RELEASE_URL}/解密ClaudeCode.epub|g" "$f"
done

# ── 部署到 GitHub Pages (gh-pages 分支) ──────────────────────
info "部署到 GitHub Pages..."

DEPLOY_DIR=$(mktemp -d)
cp -r "${OUTPUT_DIR}/"* "$DEPLOY_DIR/"

cd "$DEPLOY_DIR"
git init -q
git checkout -q -b gh-pages
git add -A
git commit -q -m "Deploy ${TAG}"
git remote add origin "git@github.com:${REPO}.git"
git push -f origin gh-pages

cd - > /dev/null
rm -rf "$DEPLOY_DIR"

info "GitHub Pages 已部署！"

# ── 创建 GitHub Release ──────────────────────────────────────
info "创建 Release ${TAG}..."

# 保存版本号
echo "$NEW_VERSION" > "$VERSION_FILE"

RELEASE_NOTES="## 解密 Claude Code ${TAG}

### 下载
- **PDF**: 解密ClaudeCode.pdf
- **EPUB**: 解密ClaudeCode.epub

### 在线阅读
https://${REPO%%/*}.github.io

---
*本书由 everettjf 使用 Claude Code 分析泄露源码编写 | 保留出处即可自由转载*"

gh release create "$TAG" \
  "$PDF_FILE" \
  "$EPUB_FILE" \
  --repo "$REPO" \
  --title "解密 Claude Code ${TAG}" \
  --notes "$RELEASE_NOTES"

info "Release 已创建！"

# ── 完成 ──────────────────────────────────────────────────────
echo ""
info "=========================================="
info "  部署完成！版本: ${TAG}"
info "=========================================="
info "  网站: https://${REPO%%/*}.github.io"
info "  Release: https://github.com/${REPO}/releases/tag/${TAG}"
info "=========================================="
