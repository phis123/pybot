#!/usr/bin/env bash
# 把上游 huggingface/pybot 的 bot/ 同步到本目录（apk/bot/）。
#
# 用法（在 apk/ 目录下执行）：
#   ./sync_bot.sh
#
# 来源：../pybot-src（huggingface/pybot 的浅克隆，上游更新后先在那里 git pull）。
# 同步后请在本地跑一次自检（见 README.md），确认 import 和一轮问答正常。
set -euo pipefail
cd "$(dirname "$0")"

SRC="../pybot-src/bot"
if [ ! -d "$SRC" ]; then
  echo "找不到 $SRC：先把 huggingface/pybot 克隆到 ../pybot-src"
  exit 1
fi

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude __pycache__ --exclude "*.pyc" "$SRC/" ./src/bot/
else
  rm -rf ./src/bot
  cp -r "$SRC" ./src/bot
  find ./src/bot -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
  find ./src/bot -name "*.pyc" -delete
fi

echo "已同步：$(find ./src/bot -name '*.py' | wc -l) 个 .py 文件，$(du -sh ./src/bot | cut -f1)"
