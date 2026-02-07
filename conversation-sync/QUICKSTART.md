# 🚀 快速開始：5分鐘設定完成

## 第一步：在你的電腦上設定（只需做一次）

```bash
# 1. Clone repository
cd ~/
git clone git@github.com:smilenccc/ai-task-tracker.git
cd ai-task-tracker

# 2. 測試連接
python3 conversation-sync/claude-code-sync.py --setup

# 應該會顯示：
# ✅ 設定完成！
```

## 第二步：在 Claude Code 中使用

### 方法 A：自動記錄（推薦）

把這段程式碼加到你的 Claude Code 啟動腳本：

```python
import sys
sys.path.append(os.path.expanduser("~/ai-task-tracker/conversation-sync"))
from claude-code-sync import ClaudeCodeSync

# 初始化
sync = ClaudeCodeSync()

# 在每次對話後自動記錄
def log_conversation(user_msg, ai_msg):
    sync.log_message("user", user_msg)
    sync.log_message("assistant", ai_msg)
    sync.sync_to_github()  # 自動同步
```

### 方法 B：手動記錄

在 Claude Code 中，每次重要對話後：

```bash
# 在 terminal 執行
cd ~/ai-task-tracker
python3 conversation-sync/claude-code-sync.py --log user "你的問題"
python3 conversation-sync/claude-code-sync.py --log assistant "AI的回答"
python3 conversation-sync/claude-code-sync.py --sync
```

## 第三步：查看 Telegram（小Linda）的對話

### 在 Claude Code 的 terminal：

```bash
# 查看小Linda 最近7天的對話
python3 conversation-sync/claude-code-sync.py --telegram 7

# 搜尋關鍵字
python3 conversation-sync/claude-code-sync.py --search "金澤旅遊" 7
```

### 或在 Claude Code 中直接問：

```
幫我看看 Telegram 上和小Linda 討論了什麼關於金澤的內容
```

然後 Claude Code 會執行：

```python
sync = ClaudeCodeSync()
sync.pull_from_github()  # 拉取最新
results = sync.get_telegram_conversations(days=7)

# 顯示相關對話
for conv in results:
    if "金澤" in conv['content']:
        print(f"{conv['timestamp']}: {conv['content']}")
```

## 在 Telegram 查看 Claude Code 的對話

直接問小Linda：

```
Linda，Claude Code 最近在討論什麼？
Linda，找找看 Claude Code 有沒有討論過 Python
```

## 常用指令速查

```bash
# 查看狀態
python3 conversation-sync/claude-code-sync.py --status

# 手動同步
python3 conversation-sync/claude-code-sync.py --sync

# 拉取最新對話
python3 conversation-sync/claude-code-sync.py --pull

# 查看 Telegram 對話
python3 conversation-sync/claude-code-sync.py --telegram 7

# 搜尋所有對話
python3 conversation-sync/claude-code-sync.py --search "關鍵字" 30
```

## 測試是否正常運作

```bash
# 1. 記錄一則測試訊息
python3 conversation-sync/claude-code-sync.py --log user "測試訊息"
python3 conversation-sync/claude-code-sync.py --sync

# 2. 等待30秒（GitHub 同步）

# 3. 在 Telegram 問小Linda：
#    "Linda，Claude Code 剛剛說了什麼？"

# 4. 如果小Linda 能看到你的測試訊息，代表成功！
```

## 故障排除

### 問題：git push 失敗

```bash
# 檢查 SSH Key
ssh -T git@github.com

# 應該顯示：Hi smilenccc! ...
```

### 問題：找不到 Telegram 對話

```bash
# 手動拉取
cd ~/ai-task-tracker
git pull origin main

# 檢查檔案
ls -la conversations/telegram/
```

### 問題：Python 模組錯誤

```bash
pip3 install --upgrade gitpython
```

## 完成！🎉

現在你的 Telegram（小Linda）和 Claude Code 可以互相看到對方的對話了！

有任何問題隨時問小Linda 💙
