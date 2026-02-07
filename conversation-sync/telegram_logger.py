#!/usr/bin/env python3
"""
Telegram 對話記錄器
小Linda 使用此腳本記錄所有 Telegram 對話
"""

import json
import os
from datetime import datetime
from pathlib import Path
import subprocess

class TelegramLogger:
    def __init__(self, base_path="/root/.openclaw/workspace/conversation-sync"):
        self.base_path = Path(base_path)
        self.conversations_dir = self.base_path / "conversations" / "telegram"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
    def log_message(self, role, content, metadata=None):
        """
        記錄一則訊息
        
        Args:
            role: "user" 或 "assistant"
            content: 訊息內容
            metadata: 額外的元資料（可選）
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.conversations_dir / f"{today}.jsonl"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "role": role,
            "content": content,
            "source": "telegram",
            "agent": "小Linda"
        }
        
        if metadata:
            entry["metadata"] = metadata
        
        # 寫入 JSONL 檔案
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ 已記錄訊息到 {log_file}")
        
        return entry
    
    def log_conversation(self, user_message, assistant_message, metadata=None):
        """
        記錄一組對話（用戶訊息 + AI 回覆）
        """
        self.log_message("user", user_message, metadata)
        self.log_message("assistant", assistant_message, metadata)
    
    def push_to_github(self, commit_message=None):
        """
        推送記錄到 GitHub
        """
        try:
            if not commit_message:
                commit_message = f"更新 Telegram 對話記錄 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Git 操作
            subprocess.run(['git', 'add', 'conversations/telegram/'], 
                         cwd=self.base_path, check=True, capture_output=True)
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.base_path,
                capture_output=True,
                text=True
            )
            
            # 如果沒有變更，跳過推送
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                print("📝 沒有新的對話需要同步")
                return False
            
            subprocess.run(['git', 'push', 'origin', 'main'], 
                         cwd=self.base_path, check=True, capture_output=True)
            
            print("✅ 對話已同步到 GitHub")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ GitHub 同步失敗: {e}")
            return False
    
    def get_today_conversations(self):
        """
        獲取今天的所有對話
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.conversations_dir / f"{today}.jsonl"
        
        if not log_file.exists():
            return []
        
        conversations = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    conversations.append(json.loads(line))
        
        return conversations
    
    def search_conversations(self, keyword, days=7):
        """
        搜尋最近 N 天的對話
        """
        results = []
        
        for i in range(days):
            date = datetime.now().date()
            from datetime import timedelta
            date = date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            log_file = self.conversations_dir / f"{date_str}.jsonl"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if keyword.lower() in entry['content'].lower():
                                results.append(entry)
        
        return results

def main():
    """
    測試用主程式
    """
    logger = TelegramLogger()
    
    # 測試記錄
    logger.log_conversation(
        user_message="測試訊息：你好",
        assistant_message="測試回覆：你好！我是小Linda",
        metadata={"test": True}
    )
    
    # 測試搜尋
    results = logger.search_conversations("測試", days=1)
    print(f"\n搜尋結果：找到 {len(results)} 則訊息")
    
    # 測試推送
    logger.push_to_github("測試：對話同步系統")

if __name__ == "__main__":
    main()
