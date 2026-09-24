#!/bin/bash
# ============================================================
# skill-creator-pro 一键打包脚本
# 版本: v1.0.0 | 许可证: MIT
#
# 功能：
#   1. 清理临时文件（__pycache__/.pyc等）
#   2. 运行规范校验（确保打包的是合格版本）
#   3. 创建带版本号的zip包
#   4. 验证zip包完整性
#   5. 输出打包报告
#
# 用法：
#   bash scripts/package.sh                    # 打包到上级目录
#   bash scripts/package.sh --output /tmp     # 指定输出目录
#   bash scripts/package.sh --skip-validate   # 跳过规范校验
#   bash scripts/package.sh --version v1.0.0  # 指定版本号（默认从SKILL.md读取）
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 默认参数
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$(dirname "$SKILL_DIR")"
SKIP_VALIDATE=false
VERSION=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --skip-validate)
            SKIP_VALIDATE=true
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --help|-h)
            echo "用法: bash scripts/package.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --output <dir>     输出目录（默认: 上级目录）"
            echo "  --skip-validate    跳过规范校验"
            echo "  --version <ver>    指定版本号（默认从SKILL.md读取）"
            echo "  --help, -h         显示帮助"
            exit 0
            ;;
        *)
            error "未知参数: $1"
            exit 2
            ;;
    esac
done

echo ""
echo "============================================================"
echo "📦 skill-creator-pro 打包脚本"
echo "============================================================"
echo ""

# 步骤1：确认技能目录
info "技能目录: $SKILL_DIR"
if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
    error "SKILL.md 不存在，不是有效的技能目录"
    exit 1
fi
ok "技能目录有效"

# 步骤2：读取版本号（使用python，更跨平台兼容）
if [ -z "$VERSION" ]; then
    VERSION=$(python3 -c "
import re, sys
try:
    with open('$SKILL_DIR/SKILL.md', 'r', encoding='utf-8') as f:
        content = f.read()
    # 匹配版本号格式：版本: v1.0.0 或 版本: 1.0.0
    m = re.search(r'版本[：:]\s*v?([0-9]+\.[0-9]+\.[0-9]+)', content)
    if m:
        print(m.group(1))
    else:
        m = re.search(r'v([0-9]+\.[0-9]+\.[0-9]+)', content)
        if m:
            print(m.group(1))
except:
    pass
" 2>/dev/null)
    if [ -z "$VERSION" ]; then
        VERSION="unknown"
        warn "无法从SKILL.md读取版本号，使用 'unknown'"
    fi
fi
info "版本号: $VERSION"

# 步骤3：清理临时文件
info "清理临时文件..."
find "$SKILL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SKILL_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$SKILL_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$SKILL_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$SKILL_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
ok "临时文件已清理"

# 步骤4：规范校验
if [ "$SKIP_VALIDATE" = false ]; then
    info "运行规范校验..."
    cd "$SKILL_DIR"
    if python3 scripts/validate_skill.py . >/dev/null 2>&1; then
        ok "规范校验通过"
    else
        error "规范校验未通过，请修复后再打包"
        error "运行: python3 scripts/validate_skill.py . 查看详情"
        exit 1
    fi
else
    warn "跳过规范校验（--skip-validate）"
fi

# 步骤5：创建zip包
SKILL_NAME=$(basename "$SKILL_DIR")
ARCHIVE_NAME="${SKILL_NAME}-${VERSION}.zip"
ARCHIVE_PATH="$OUTPUT_DIR/$ARCHIVE_NAME"

info "创建压缩包: $ARCHIVE_PATH"
mkdir -p "$OUTPUT_DIR"

# 切换到上级目录，确保zip包内路径正确
cd "$(dirname "$SKILL_DIR")"
zip -r -q "$ARCHIVE_PATH" "$SKILL_NAME/" \
    -x "*/__pycache__/*" \
    -x "*.pyc" \
    -x "*.pyo" \
    -x "*/.pytest_cache/*" \
    -x "*/.git/*"

if [ ! -f "$ARCHIVE_PATH" ]; then
    error "压缩包创建失败"
    exit 3
fi
ok "压缩包创建成功"

# 步骤6：验证zip包完整性
info "验证压缩包完整性..."
if unzip -tq "$ARCHIVE_PATH" >/dev/null 2>&1; then
    ok "压缩包完整性验证通过"
else
    error "压缩包完整性验证失败"
    exit 3
fi

# 步骤7：统计信息
FILE_COUNT=$(unzip -l "$ARCHIVE_PATH" | tail -1 | awk '{print $2}')
ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
UNCOMPRESSED_SIZE=$(unzip -l "$ARCHIVE_PATH" | tail -1 | awk '{print $1}')

# 步骤8：输出打包报告
echo ""
echo "============================================================"
echo "✅ 打包完成"
echo "============================================================"
echo ""
echo "  📄 包名:     $ARCHIVE_NAME"
echo "  📍 路径:     $ARCHIVE_PATH"
echo "  📦 大小:     $ARCHIVE_SIZE"
echo "  📁 文件数:   $FILE_COUNT"
echo "  🏷️  版本:     $VERSION"
echo ""
echo "  📋 包内容:"
unzip -l "$ARCHIVE_PATH" | grep -E "SKILL.md|LICENSE|CHANGELOG|scripts/|references/" | head -20
echo ""
echo "  🚀 安装方法:"
echo "    1. 解压到 workspace/.user_skills/ 目录"
echo "    2. unzip $ARCHIVE_NAME -d /path/to/workspace/.user_skills/"
echo "    3. 重启Agent会话，技能即可加载"
echo ""
echo "============================================================"

exit 0
