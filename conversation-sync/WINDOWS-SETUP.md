# 🪟 Windows 設定指南

## 前置需求

確認你的 Windows 電腦已安裝：
- ✅ Git（https://git-scm.com/download/win）
- ✅ Python 3.8+（https://www.python.org/downloads/）
- ✅ GitHub SSH Key（用於 git 操作）

## 快速設定（5分鐘完成）

### 第一步：Clone Repository

**使用 PowerShell 或 Command Prompt：**

```powershell
# 進入你的用戶目錄
cd %USERPROFILE%

# Clone repository
git clone git@github.com:smilenccc/ai-task-tracker.git

# 進入資料夾
cd ai-task-tracker
```

### 第二步：初始化系統

```powershell
python conversation-sync\claude-code-sync.py --setup
```

**應該會看到：**
```
🔧 初始化 Claude Code 同步工具...
✅ 設定完成！
📁 對話記錄位置: C:\Users\你的用戶名\ai-task-tracker\conversation-sync\conversations\claude-code
```

### 第三步：測試系統

```powershell
# 記錄測試訊息
python conversation-sync\claude-code-sync.py --log user "測試：Windows系統運作中"
python conversation-sync\claude-code-sync.py --sync
```

### 第四步：查看 Telegram 對話

```powershell
# 查看小Linda 最近7天的對話
python conversation-sync\claude-code-sync.py --telegram 7

# 搜尋關鍵字
python conversation-sync\claude-code-sync.py --search "金澤" 7
```

## 常用指令（Windows 版）

```powershell
# 進入專案目錄（每次使用前）
cd %USERPROFILE%\ai-task-tracker

# 查看系統狀態
python conversation-sync\claude-code-sync.py --status

# 記錄對話
python conversation-sync\claude-code-sync.py --log user "你的問題"
python conversation-sync\claude-code-sync.py --log assistant "AI回答"

# 同步到 GitHub
python conversation-sync\claude-code-sync.py --sync

# 拉取最新對話
python conversation-sync\claude-code-sync.py --pull

# 查看 Telegram 對話
python conversation-sync\claude-code-sync.py --telegram 7

# 搜尋所有對話
python conversation-sync\claude-code-sync.py --search "關鍵字" 30
```

## 建立快捷指令（可選）

### 方法 A：建立批次檔

在 `ai-task-tracker` 資料夾建立 `sync-claude.bat`：

```batch
@echo off
cd /d %USERPROFILE%\ai-task-tracker
python conversation-sync\claude-code-sync.py %*
pause
```

之後就可以這樣用：

```powershell
# 直接執行
sync-claude.bat --telegram 7
sync-claude.bat --sync
```

### 方法 B：PowerShell 函數

在 PowerShell 配置檔加入：

```powershell
# 編輯配置檔
notepad $PROFILE

# 加入這段：
function sync-claude {
    python "$env:USERPROFILE\ai-task-tracker\conversation-sync\claude-code-sync.py" $args
}
```

重新啟動 PowerShell 後就可以：

```powershell
sync-claude --telegram 7
sync-claude --sync
```

## Claude Code 整合（Windows）

### 自動記錄腳本

在 Claude Code 專案中建立 `log-conversation.py`：

```python
import sys
import os
import subprocess

def log_to_sync(role, message):
    """記錄對話到同步系統"""
    repo_path = os.path.join(os.path.expanduser('~'), 'ai-task-tracker')
    script_path = os.path.join(repo_path, 'conversation-sync', 'claude-code-sync.py')
    
    # 記錄訊息
    subprocess.run(['python', script_path, '--log', role, message], check=True)
    
    # 同步
    subprocess.run(['python', script_path, '--sync'], check=True)
    
    print(f"✅ 已記錄並同步 {role} 訊息")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方式: python log-conversation.py [user|assistant] [訊息內容]")
        sys.exit(1)
    
    role = sys.argv[1]
    message = sys.argv[2]
    log_to_sync(role, message)
```

使用方式：

```powershell
python log-conversation.py user "我的問題"
python log-conversation.py assistant "AI的回答"
```

## 查看 Telegram 對話（進階）

### 建立查看器腳本

在 `ai-task-tracker` 建立 `view-telegram.py`：

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'conversation-sync'))

from claude_code_sync import ClaudeCodeSync
import argparse

def main():
    parser = argparse.ArgumentParser(description='查看 Telegram 對話')
    parser.add_argument('--days', type=int, default=7, help='查看最近幾天')
    parser.add_argument('--search', type=str, help='搜尋關鍵字')
    
    args = parser.parse_args()
    
    repo_path = os.path.dirname(os.path.abspath(__file__))
    sync = ClaudeCodeSync(repo_path)
    
    # 先拉取最新
    print("📥 拉取最新對話...")
    sync.pull_from_github()
    
    if args.search:
        # 搜尋
        results = sync.search_all_conversations(args.search, args.days)
        print(f"\n🔍 搜尋結果：'{args.search}'\n")
        print("=" * 80)
        
        if results['telegram']:
            print(f"\n📱 Telegram（{len(results['telegram'])} 則）：\n")
            for entry in results['telegram'][-10:]:
                print(sync.format_conversation(entry))
    else:
        # 顯示最近對話
        sync.display_recent_telegram(args.days)

if __name__ == "__main__":
    main()
```

使用：

```powershell
# 查看最近7天
python view-telegram.py --days 7

# 搜尋關鍵字
python view-telegram.py --search "金澤" --days 30
```

## 排程自動同步（可選）

### 使用 Windows 工作排程器

1. 開啟「工作排程器」（Task Scheduler）
2. 建立基本工作
3. 設定：
   - **觸發程序**：每小時一次
   - **動作**：啟動程式
   - **程式**：`python`
   - **參數**：`conversation-sync\claude-code-sync.py --pull`
   - **起始於**：`C:\Users\你的用戶名\ai-task-tracker`

這樣就會每小時自動拉取最新的 Telegram 對話。

## 常見問題（Windows 特有）

### Q: 路徑有空格怎麼辦？

```powershell
# 使用引號
cd "C:\Users\My Name\ai-task-tracker"
python "conversation-sync\claude-code-sync.py" --status
```

### Q: Python 找不到怎麼辦？

```powershell
# 確認 Python 安裝
python --version

# 如果找不到，試試：
py --version

# 或使用完整路徑
C:\Python39\python.exe conversation-sync\claude-code-sync.py --status
```

### Q: Git push 需要密碼？

確認使用 SSH key 而不是 HTTPS：

```powershell
cd %USERPROFILE%\ai-task-tracker
git remote -v

# 應該顯示：
# origin  git@github.com:smilenccc/ai-task-tracker.git (fetch)
# origin  git@github.com:smilenccc/ai-task-tracker.git (push)

# 如果是 https，改成 ssh：
git remote set-url origin git@github.com:smilenccc/ai-task-tracker.git
```

### Q: 權限錯誤？

用管理員身分執行 PowerShell：
1. 搜尋 PowerShell
2. 右鍵 → 以系統管理員身分執行

## 測試完整流程

```powershell
# 1. 進入目錄
cd %USERPROFILE%\ai-task-tracker

# 2. 拉取最新
python conversation-sync\claude-code-sync.py --pull

# 3. 記錄測試訊息
python conversation-sync\claude-code-sync.py --log user "Windows 測試成功！"
python conversation-sync\claude-code-sync.py --sync

# 4. 查看 Telegram 對話
python conversation-sync\claude-code-sync.py --telegram 1

# 5. 在 Telegram 問小Linda：
#    "Linda，Claude Code 剛剛說了什麼？"
```

## 完成！🎉

現在你的 Windows 電腦上的 Claude Code 可以和 Telegram 的小Linda 完全同步對話了！

有任何問題隨時問小Linda！💙

---

**小提示：**
- 建議將 `ai-task-tracker` 資料夾加到「快速存取」
- 可以建立桌面捷徑方便開啟
- 使用 VS Code 的話，可以直接在終端機執行這些指令
