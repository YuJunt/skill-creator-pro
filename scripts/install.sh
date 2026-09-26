#!/bin/bash
# 技能一键安装脚本
# 用法: bash install.sh <skill-path> [target-dir]
#   默认安装到 ~/.claude/skills/ 或指定目录

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="$(basename "$SCRIPT_DIR")"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()    { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 目标目录
TARGET="${1:-$HOME/.claude/skills}"

echo "📦 安装技能: $SKILL_NAME"
echo "   目标: $TARGET"
echo ""

# 检查源目录
if [ ! -f "$SCRIPT_DIR/SKILL.md" ]; then
    error "未找到SKILL.md，无法安装"
    exit 1
fi

# 创建目标目录
mkdir -p "$TARGET"

# 复制技能
DEST="$TARGET/$SKILL_NAME"
if [ -d "$DEST" ]; then
    warn "目标已存在: $DEST"
    read -p "覆盖? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "已取消"
        exit 0
    fi
    rm -rf "$DEST"
fi

cp -r "$SCRIPT_DIR" "$DEST"
ok "技能已安装到: $DEST"

# 清理
rm -rf "$DEST/__pycache__" "$DEST/scripts/__pycache__"
find "$DEST" -name "*.pyc" -delete 2>/dev/null || true

# 验证
if [ -f "$DEST/SKILL.md" ]; then
    ok "安装验证通过"
else
    error "安装失败：SKILL.md未复制"
    exit 1
fi

echo ""
echo "✅ 安装完成！技能 '$SKILL_NAME' 现在可用。"
