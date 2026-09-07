#!/bin/bash
# 画像サイズチェックスクリプト
# コミット前に実行して、問題のある画像を検出する
#
# 使い方:
#   bash scripts/check-images.sh
#   bash scripts/check-images.sh public/images/slug-sec01.webp  # 特定ファイルだけ

set -e

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

errors=0
warnings=0

check_image() {
  local f="$1"
  local name
  name=$(basename "$f")

  local result
  result=$(python3 -c "
from PIL import Image
img = Image.open('$f')
import os
size_kb = os.path.getsize('$f') / 1024
print(f'{img.width} {img.height} {size_kb:.0f}')
" 2>/dev/null)

  if [ -z "$result" ]; then
    echo -e "${RED}ERROR${NC} $name: 読み込めません"
    ((errors++))
    return
  fi

  local w h kb
  w=$(echo "$result" | awk '{print $1}')
  h=$(echo "$result" | awk '{print $2}')
  kb=$(echo "$result" | awk '{print $3}')
  local ratio
  ratio=$(python3 -c "print(f'{$h/$w:.1f}')")

  local status="ok"
  local msgs=()

  # ratio > 2.0 はエラー
  if python3 -c "exit(0 if $h > $w * 2 else 1)"; then
    msgs+=("ratio=${ratio} (上限2.0)")
    status="error"
  fi

  # 幅2000px超は警告
  if [ "$w" -gt 2000 ]; then
    msgs+=("幅${w}px (1600px推奨)")
    if [ "$status" = "ok" ]; then status="warn"; fi
  fi

  # 150KB超は警告（アイキャッチ除く）
  if echo "$name" | grep -q "\-sec"; then
    if python3 -c "exit(0 if $kb > 150 else 1)"; then
      msgs+=("${kb}KB (150KB推奨)")
      if [ "$status" = "ok" ]; then status="warn"; fi
    fi
  fi

  case "$status" in
    error)
      echo -e "${RED}ERROR${NC} $name: ${w}x${h} ${kb}KB - ${msgs[*]}"
      ((errors++))
      ;;
    warn)
      echo -e "${YELLOW}WARN ${NC} $name: ${w}x${h} ${kb}KB - ${msgs[*]}"
      ((warnings++))
      ;;
    *)
      echo -e "${GREEN}OK   ${NC} $name: ${w}x${h} ${kb}KB"
      ;;
  esac
}

# ファイル指定があればそれだけ、なければ全画像
if [ $# -gt 0 ]; then
  for f in "$@"; do
    check_image "$f"
  done
else
  for f in public/images/*.webp; do
    [ -f "$f" ] || continue
    check_image "$f"
  done
fi

echo ""
if [ $errors -gt 0 ]; then
  echo -e "${RED}$errors 件のエラーがあります。修正してからコミットしてください。${NC}"
  exit 1
elif [ $warnings -gt 0 ]; then
  echo -e "${YELLOW}$warnings 件の警告があります。確認してください。${NC}"
  exit 0
else
  echo -e "${GREEN}問題ありません。${NC}"
  exit 0
fi
