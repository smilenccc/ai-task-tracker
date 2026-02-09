#!/usr/bin/env python3
"""
公司電腦 Claude Code 對話同步腳本
自動記錄對話並同步到 GitHub
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess

# 設定路徑
REPO_DIR = Path.home() / "Documents" / "ai-task-tracker"
CONV_DIR = REPO_DIR / "conversation-sync" / "conversations" / "claude-code-work"


def ensure_dir():
    """確保對話目錄存在"""
    CONV_DIR.mkdir(parents=True, exist_ok=True)


def get_today_file():
    """取得今天的對話檔案路徑"""
    today = datetime.now().strftime("%Y-%m-%d")
    return CONV_DIR / f"{today}.jsonl"


def log_conversation(role, content, metadata=None):
    """記錄一則對話"""
    ensure_dir()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content,
        "source": "claude-code-work",
        "agent": "Claude Code (Work)"
    }

    if metadata:
        entry["metadata"] = metadata

    with open(get_today_file(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Logged: [{role}] {content[:50]}...")
    return entry


def sync_to_github(commit_message=None):
    """同步到 GitHub"""
    try:
        os.chdir(REPO_DIR)
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        subprocess.run(["git", "add", "conversation-sync/conversations/"], check=True)

        if not commit_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            commit_message = f"Sync work conversations - {timestamp}"

        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True, text=True
        )

        if "nothing to commit" in (result.stdout + result.stderr).lower():
            print("No new conversations to sync")
            return False

        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Synced to GitHub successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Sync failed: {e}")
        return False


def pull_latest():
    """拉取最新對話"""
    try:
        os.chdir(REPO_DIR)
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        print("Pulled latest conversations")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Pull failed: {e}")
        return False


def read_conversations(source="telegram", days=3):
    """讀取指定來源的對話"""
    from datetime import timedelta
    conversations = []
    base_dir = REPO_DIR / "conversation-sync" / "conversations" / source

    for i in range(days):
        date = (datetime.now().date() - timedelta(days=i))
        file_path = base_dir / f"{date.strftime('%Y-%m-%d')}.jsonl"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        conversations.append(json.loads(line))

    return conversations


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sync_work_conversations.py pull        - Pull latest")
        print("  python sync_work_conversations.py sync        - Push to GitHub")
        print("  python sync_work_conversations.py log ROLE MSG - Log a message")
        print("  python sync_work_conversations.py read SOURCE  - Read conversations")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "pull":
        pull_latest()
    elif cmd == "sync":
        sync_to_github()
    elif cmd == "log" and len(sys.argv) >= 4:
        log_conversation(sys.argv[2], sys.argv[3])
    elif cmd == "read":
        source = sys.argv[2] if len(sys.argv) > 2 else "telegram"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        convs = read_conversations(source, days)
        for c in convs:
            ts = c["timestamp"][:19].replace("T", " ")
            role = c.get("agent", c["role"])
            print(f"[{ts}] {role}: {c['content']}")
    else:
        print(f"Unknown command: {cmd}")
