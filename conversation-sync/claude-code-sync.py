#!/usr/bin/env python3
"""
Claude Code 對話同步工具
在本地電腦上運行，記錄 Claude Code 的對話並同步到 GitHub
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import argparse

class ClaudeCodeSync:
    def __init__(self, repo_path=None):
        """
        初始化同步工具
        
        Args:
            repo_path: GitHub repository 的本地路徑
        """
        if repo_path is None:
            # 預設路徑
            home = Path.home()
            repo_path = home / "ai-task-tracker"
        
        self.repo_path = Path(repo_path)
        self.conversations_dir = self.repo_path / "conversations" / "claude-code"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        self.telegram_dir = self.repo_path / "conversations" / "telegram"
    
    def log_message(self, role, content, metadata=None):
        """
        記錄一則 Claude Code 訊息
        
        Args:
            role: "user" 或 "assistant"
            content: 訊息內容
            metadata: 額外資訊
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.conversations_dir / f"{today}.jsonl"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "role": role,
            "content": content,
            "source": "claude-code",
            "agent": "Claude Code"
        }
        
        if metadata:
            entry["metadata"] = metadata
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ 已記錄訊息")
        return entry
    
    def sync_to_github(self, commit_message=None):
        """
        同步到 GitHub
        """
        try:
            if not commit_message:
                commit_message = f"更新 Claude Code 對話 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 先 pull 最新的變更
            subprocess.run(['git', 'pull', 'origin', 'main'], 
                         cwd=self.repo_path, check=True)
            
            # 提交變更
            subprocess.run(['git', 'add', 'conversations/claude-code/'], 
                         cwd=self.repo_path, check=True)
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if "nothing to commit" not in result.stdout.lower():
                subprocess.run(['git', 'push', 'origin', 'main'], 
                             cwd=self.repo_path, check=True)
                print("✅ 已同步到 GitHub")
                return True
            else:
                print("📝 沒有新的對話需要同步")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 同步失敗: {e}")
            return False
    
    def pull_from_github(self):
        """
        從 GitHub 拉取最新的對話（包含 Telegram 的）
        """
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'], 
                         cwd=self.repo_path, check=True)
            print("✅ 已拉取最新對話")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 拉取失敗: {e}")
            return False
    
    def get_telegram_conversations(self, days=7):
        """
        獲取 Telegram（小Linda）最近的對話
        """
        conversations = []
        
        for i in range(days):
            date = datetime.now().date()
            from datetime import timedelta
            date = date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            log_file = self.telegram_dir / f"{date_str}.jsonl"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            conversations.append(json.loads(line))
        
        return conversations
    
    def search_all_conversations(self, keyword, days=30):
        """
        搜尋所有對話（Telegram + Claude Code）
        """
        results = {"telegram": [], "claude-code": []}
        
        for i in range(days):
            date = datetime.now().date()
            from datetime import timedelta
            date = date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # 搜尋 Telegram
            tg_file = self.telegram_dir / f"{date_str}.jsonl"
            if tg_file.exists():
                with open(tg_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if keyword.lower() in entry['content'].lower():
                                results["telegram"].append(entry)
            
            # 搜尋 Claude Code
            cc_file = self.conversations_dir / f"{date_str}.jsonl"
            if cc_file.exists():
                with open(cc_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if keyword.lower() in entry['content'].lower():
                                results["claude-code"].append(entry)
        
        return results
    
    def format_conversation(self, entry):
        """
        格式化對話顯示
        """
        timestamp = entry['timestamp'][:19].replace('T', ' ')
        role = "你" if entry['role'] == "user" else entry.get('agent', 'AI')
        content = entry['content']
        
        return f"[{timestamp}] {role}: {content}"
    
    def display_recent_telegram(self, days=7):
        """
        顯示 Telegram 最近的對話
        """
        print(f"\n📱 Telegram（小Linda）最近 {days} 天的對話：\n")
        print("=" * 80)
        
        conversations = self.get_telegram_conversations(days)
        
        if not conversations:
            print("（尚無對話記錄）")
            return
        
        for entry in conversations[-20:]:  # 只顯示最近20則
            print(self.format_conversation(entry))
        
        print("\n" + "=" * 80)
        print(f"總共 {len(conversations)} 則訊息")

def main():
    parser = argparse.ArgumentParser(description="Claude Code 對話同步工具")
    parser.add_argument('--setup', action='store_true', help='初始化設定')
    parser.add_argument('--log', nargs=2, metavar=('ROLE', 'MESSAGE'), help='記錄訊息')
    parser.add_argument('--sync', action='store_true', help='同步到 GitHub')
    parser.add_argument('--pull', action='store_true', help='從 GitHub 拉取')
    parser.add_argument('--status', action='store_true', help='查看狀態')
    parser.add_argument('--telegram', type=int, metavar='DAYS', help='查看 Telegram 對話')
    parser.add_argument('--search', nargs=2, metavar=('KEYWORD', 'DAYS'), help='搜尋對話')
    parser.add_argument('--repo', type=str, help='Repository 路徑')
    
    args = parser.parse_args()
    
    sync = ClaudeCodeSync(args.repo)
    
    if args.setup:
        print("🔧 初始化 Claude Code 同步工具...")
        sync.pull_from_github()
        print("✅ 設定完成！")
        print(f"📁 對話記錄位置: {sync.conversations_dir}")
        print("\n使用範例：")
        print("  python3 claude-code-sync.py --log user '你好'")
        print("  python3 claude-code-sync.py --sync")
        print("  python3 claude-code-sync.py --telegram 7")
        
    elif args.log:
        role, message = args.log
        sync.log_message(role, message)
        sync.sync_to_github()
        
    elif args.sync:
        sync.sync_to_github()
        
    elif args.pull:
        sync.pull_from_github()
        
    elif args.status:
        print("📊 同步系統狀態\n")
        print(f"Repository: {sync.repo_path}")
        print(f"Claude Code 對話: {sync.conversations_dir}")
        print(f"Telegram 對話: {sync.telegram_dir}")
        
        today = datetime.now().strftime("%Y-%m-%d")
        cc_today = sync.conversations_dir / f"{today}.jsonl"
        tg_today = sync.telegram_dir / f"{today}.jsonl"
        
        cc_count = 0
        if cc_today.exists():
            with open(cc_today, 'r') as f:
                cc_count = len(f.readlines())
        
        tg_count = 0
        if tg_today.exists():
            with open(tg_today, 'r') as f:
                tg_count = len(f.readlines())
        
        print(f"\n今日對話統計：")
        print(f"  Claude Code: {cc_count} 則")
        print(f"  Telegram: {tg_count} 則")
        
    elif args.telegram:
        sync.pull_from_github()  # 先拉取最新的
        sync.display_recent_telegram(args.telegram)
        
    elif args.search:
        keyword, days = args.search
        sync.pull_from_github()
        results = sync.search_all_conversations(keyword, int(days))
        
        print(f"\n🔍 搜尋結果：'{keyword}'\n")
        print("=" * 80)
        
        if results['telegram']:
            print(f"\n📱 Telegram（{len(results['telegram'])} 則）：\n")
            for entry in results['telegram'][-10:]:
                print(sync.format_conversation(entry))
        
        if results['claude-code']:
            print(f"\n💻 Claude Code（{len(results['claude-code'])} 則）：\n")
            for entry in results['claude-code'][-10:]:
                print(sync.format_conversation(entry))
        
        if not results['telegram'] and not results['claude-code']:
            print("（沒有找到相關對話）")
        
        print("\n" + "=" * 80)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
