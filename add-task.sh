#!/bin/bash

# AI 任務新增腳本
# 使用方式: ./add-task.sh "任務標題" "任務描述" "類型" "狀態"

TITLE="$1"
DESC="$2"
CATEGORY="${3:-其他}"
STATUS="${4:-pending}"

if [ -z "$TITLE" ]; then
    echo "錯誤：需要提供任務標題"
    echo "使用方式: ./add-task.sh \"任務標題\" \"任務描述\" \"類型\" \"狀態\""
    exit 1
fi

# 進入專案目錄
cd "$(dirname "$0")"

# 讀取現有任務
if [ ! -f "tasks.json" ]; then
    echo '{"tasks":[],"lastUpdated":""}' > tasks.json
fi

# 生成新任務 ID
NEW_ID=$(jq '.tasks | length + 1' tasks.json)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# 新增任務
jq --arg id "$NEW_ID" \
   --arg title "$TITLE" \
   --arg desc "$DESC" \
   --arg cat "$CATEGORY" \
   --arg status "$STATUS" \
   --arg time "$TIMESTAMP" \
   '.tasks += [{
     "id": ($id | tonumber),
     "title": $title,
     "description": $desc,
     "category": $cat,
     "status": $status,
     "createdAt": $time,
     "updatedAt": $time,
     "source": "telegram"
   }] | .lastUpdated = $time' tasks.json > tasks.json.tmp

mv tasks.json.tmp tasks.json

# 推送到 GitHub
git add tasks.json
git commit -m "新增任務: $TITLE"
git push origin main

echo "✅ 任務已新增並推送到 GitHub"
echo "🌐 查看網站: https://smilenccc.github.io/ai-task-tracker/"
