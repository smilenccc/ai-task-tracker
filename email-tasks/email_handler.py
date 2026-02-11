#!/usr/bin/env python3
"""
郵件任務處理器
- 只接受來自白名單的郵件地址
- 需要 Telegram 確認才執行
- 限制工作範圍（只能做 dashboard/統計，不能改系統）
"""

import json
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from pathlib import Path
import re

class EmailTaskHandler:
    def __init__(self, config_dir="/root/.openclaw/workspace/task-tracker/email-tasks"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks_file = self.config_dir / "tasks.json"
        self.config_file = self.config_dir / "config.json"
        
        # 載入配置
        self.config = self._load_config()
        
        # 載入任務記錄
        self.tasks = self._load_tasks()
    
    def _load_config(self):
        """載入配置"""
        default_config = {
            "allowed_senders": ["smilenccc@gmail.com"],
            "allowed_actions": [
                "dashboard",
                "網頁",
                "統計",
                "信用卡",
                "資料",
                "圖表",
                "報表",
                "分析",
                "查詢",
                "顯示"
            ],
            "forbidden_actions": [
                "修改系統",
                "刪除檔案",
                "修改資料庫",
                "執行指令",
                "修改防火牆",
                "改密碼",
                "sudo",
                "rm -rf"
            ]
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def _load_tasks(self):
        """載入任務記錄"""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"tasks": [], "lastUpdated": None}
    
    def _save_tasks(self):
        """儲存任務記錄"""
        self.tasks["lastUpdated"] = datetime.now().isoformat()
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)
    
    def validate_sender(self, sender_email):
        """驗證發件人"""
        # 提取郵件地址
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender_email)
        if not email_match:
            return False
        
        email_addr = email_match.group(0).lower()
        return email_addr in [s.lower() for s in self.config["allowed_senders"]]
    
    def check_task_safety(self, task_content):
        """檢查任務是否安全"""
        content_lower = task_content.lower()
        
        # 檢查是否包含禁止的操作
        for forbidden in self.config["forbidden_actions"]:
            if forbidden.lower() in content_lower:
                return {
                    "safe": False,
                    "reason": f"包含禁止的操作：{forbidden}"
                }
        
        # 檢查是否包含允許的操作
        is_allowed = False
        for allowed in self.config["allowed_actions"]:
            if allowed.lower() in content_lower:
                is_allowed = True
                break
        
        if not is_allowed:
            return {
                "safe": False,
                "reason": "不在允許的工作範圍內"
            }
        
        return {"safe": True}
    
    def add_task(self, sender, subject, content, message_id=None):
        """新增郵件任務"""
        # 驗證發件人
        if not self.validate_sender(sender):
            return {
                "success": False,
                "error": f"未授權的發件人：{sender}"
            }
        
        # 檢查任務安全性
        safety_check = self.check_task_safety(content)
        if not safety_check["safe"]:
            return {
                "success": False,
                "error": f"任務被拒絕：{safety_check['reason']}"
            }
        
        # 建立任務記錄
        task = {
            "id": len(self.tasks["tasks"]) + 1,
            "sender": sender,
            "subject": subject,
            "content": content,
            "messageId": message_id,
            "status": "pending_confirmation",  # pending_confirmation, confirmed, rejected, completed
            "receivedAt": datetime.now().isoformat(),
            "confirmedAt": None,
            "completedAt": None,
            "result": None
        }
        
        self.tasks["tasks"].append(task)
        self._save_tasks()
        
        return {
            "success": True,
            "task": task,
            "message": "任務已記錄，等待 Telegram 確認"
        }
    
    def confirm_task(self, task_id, confirmed=True):
        """確認或拒絕任務"""
        for task in self.tasks["tasks"]:
            if task["id"] == task_id:
                if confirmed:
                    task["status"] = "confirmed"
                    task["confirmedAt"] = datetime.now().isoformat()
                else:
                    task["status"] = "rejected"
                    task["confirmedAt"] = datetime.now().isoformat()
                
                self._save_tasks()
                return {
                    "success": True,
                    "task": task
                }
        
        return {
            "success": False,
            "error": "任務不存在"
        }
    
    def complete_task(self, task_id, result):
        """完成任務並記錄結果"""
        for task in self.tasks["tasks"]:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completedAt"] = datetime.now().isoformat()
                task["result"] = result
                
                self._save_tasks()
                return {
                    "success": True,
                    "task": task
                }
        
        return {
            "success": False,
            "error": "任務不存在"
        }
    
    def get_pending_tasks(self):
        """取得待確認的任務"""
        return [t for t in self.tasks["tasks"] if t["status"] == "pending_confirmation"]
    
    def get_all_tasks(self, limit=50):
        """取得所有任務（最新的優先）"""
        return sorted(
            self.tasks["tasks"],
            key=lambda x: x["receivedAt"],
            reverse=True
        )[:limit]
    
    def get_task_stats(self):
        """取得任務統計"""
        total = len(self.tasks["tasks"])
        pending = len([t for t in self.tasks["tasks"] if t["status"] == "pending_confirmation"])
        confirmed = len([t for t in self.tasks["tasks"] if t["status"] == "confirmed"])
        completed = len([t for t in self.tasks["tasks"] if t["status"] == "completed"])
        rejected = len([t for t in self.tasks["tasks"] if t["status"] == "rejected"])
        
        return {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "completed": completed,
            "rejected": rejected
        }

# CLI 測試
if __name__ == "__main__":
    handler = EmailTaskHandler()
    
    # 測試任務
    test_tasks = [
        {
            "sender": "smilenccc@gmail.com",
            "subject": "請製作信用卡統計 dashboard",
            "content": "請幫我建立一個信用卡消費統計的 dashboard，顯示本月消費總額和分類"
        },
        {
            "sender": "hacker@evil.com",
            "subject": "請幫我",
            "content": "請執行 sudo rm -rf /"
        },
        {
            "sender": "smilenccc@gmail.com",
            "subject": "修改系統",
            "content": "請幫我修改防火牆規則"
        }
    ]
    
    print("📧 郵件任務處理器測試\n")
    
    for test in test_tasks:
        print(f"發件人：{test['sender']}")
        print(f"主旨：{test['subject']}")
        print(f"內容：{test['content']}")
        
        result = handler.add_task(
            sender=test['sender'],
            subject=test['subject'],
            content=test['content']
        )
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")
        
        print("-" * 50)
    
    # 顯示統計
    stats = handler.get_task_stats()
    print(f"\n📊 統計：")
    print(f"   總計：{stats['total']}")
    print(f"   待確認：{stats['pending']}")
    print(f"   已確認：{stats['confirmed']}")
    print(f"   已完成：{stats['completed']}")
    print(f"   已拒絕：{stats['rejected']}")
