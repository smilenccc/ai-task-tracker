#!/usr/bin/env python3
"""
AI 任務新增腳本（Python 版本）
可以直接從 Python 程式呼叫
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class TaskManager:
    def __init__(self, repo_path="/root/.openclaw/workspace/task-tracker"):
        self.repo_path = Path(repo_path)
        self.tasks_file = self.repo_path / "tasks.json"
    
    def load_tasks(self):
        """載入現有任務"""
        if not self.tasks_file.exists():
            return {"tasks": [], "lastUpdated": ""}
        
        with open(self.tasks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_tasks(self, data):
        """儲存任務資料"""
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_task(self, title, description="", category="其他", status="pending"):
        """新增任務"""
        data = self.load_tasks()
        
        # 生成新 ID
        new_id = len(data["tasks"]) + 1
        
        # 生成時間戳
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # 建立新任務
        new_task = {
            "id": new_id,
            "title": title,
            "description": description,
            "category": category,
            "status": status,
            "createdAt": timestamp,
            "updatedAt": timestamp,
            "source": "telegram"
        }
        
        # 新增到列表
        data["tasks"].append(new_task)
        data["lastUpdated"] = timestamp
        
        # 儲存
        self.save_tasks(data)
        
        return new_task
    
    def update_task_status(self, task_id, status):
        """更新任務狀態"""
        data = self.load_tasks()
        
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = status
                task["updatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                break
        
        data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        self.save_tasks(data)
    
    def push_to_github(self, commit_message="更新任務資料"):
        """推送到 GitHub"""
        try:
            subprocess.run(
                ["git", "add", "tasks.json"],
                cwd=self.repo_path,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True
            )
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.repo_path,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 操作失敗: {e}", file=sys.stderr)
            return False

def main():
    """命令列介面"""
    if len(sys.argv) < 2:
        print("使用方式: python3 add_task.py <標題> [描述] [類型] [狀態]")
        sys.exit(1)
    
    title = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""
    category = sys.argv[3] if len(sys.argv) > 3 else "其他"
    status = sys.argv[4] if len(sys.argv) > 4 else "pending"
    
    manager = TaskManager()
    task = manager.add_task(title, description, category, status)
    
    print(f"✅ 任務已新增:")
    print(f"   ID: {task['id']}")
    print(f"   標題: {task['title']}")
    print(f"   狀態: {task['status']}")
    
    if manager.push_to_github(f"新增任務: {title}"):
        print("✅ 已推送到 GitHub")
        print("🌐 查看網站: https://smilenccc.github.io/ai-task-tracker/")
    else:
        print("⚠️ 推送失敗，請手動檢查")

if __name__ == "__main__":
    main()
