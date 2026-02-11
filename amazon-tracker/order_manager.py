#!/usr/bin/env python3
"""
Amazon 訂單管理器
可以新增、刪除、查詢訂單
"""

import json
from datetime import datetime
from pathlib import Path

class OrderManager:
    def __init__(self, orders_file="orders.json"):
        self.orders_file = Path(orders_file)
        self.orders_data = self._load_orders()
    
    def _load_orders(self):
        """載入訂單資料"""
        if self.orders_file.exists():
            with open(self.orders_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"orders": [], "lastUpdated": None}
    
    def _save_orders(self):
        """儲存訂單資料"""
        self.orders_data["lastUpdated"] = datetime.now().isoformat()
        with open(self.orders_file, 'w', encoding='utf-8') as f:
            json.dump(self.orders_data, f, indent=2, ensure_ascii=False)
    
    def add_order(self, order_number, tracking_number, carrier="Unknown", product_name=""):
        """新增訂單"""
        # 檢查是否已存在
        for order in self.orders_data["orders"]:
            if order["orderNumber"] == order_number:
                return {
                    "success": False,
                    "error": "訂單已存在"
                }
        
        # 生成新 ID
        new_id = max([o["id"] for o in self.orders_data["orders"]], default=0) + 1
        
        # 建立訂單
        new_order = {
            "id": new_id,
            "orderNumber": order_number,
            "trackingNumber": tracking_number,
            "carrier": carrier,
            "productName": product_name,
            "status": "pending",
            "currentLocation": "未知",
            "destination": "台中市大里區",
            "addedAt": datetime.now().isoformat(),
            "lastUpdate": datetime.now().isoformat()
        }
        
        self.orders_data["orders"].append(new_order)
        self._save_orders()
        
        return {
            "success": True,
            "order": new_order,
            "message": f"✅ 訂單已新增：{order_number}"
        }
    
    def remove_order(self, order_id):
        """刪除訂單"""
        original_count = len(self.orders_data["orders"])
        self.orders_data["orders"] = [
            o for o in self.orders_data["orders"] if o["id"] != order_id
        ]
        
        if len(self.orders_data["orders"]) < original_count:
            self._save_orders()
            return {
                "success": True,
                "message": f"✅ 訂單已刪除 (ID: {order_id})"
            }
        
        return {
            "success": False,
            "error": "訂單不存在"
        }
    
    def update_order_status(self, order_id, status, current_location=None):
        """更新訂單狀態"""
        for order in self.orders_data["orders"]:
            if order["id"] == order_id:
                order["status"] = status
                if current_location:
                    order["currentLocation"] = current_location
                order["lastUpdate"] = datetime.now().isoformat()
                self._save_orders()
                return {
                    "success": True,
                    "order": order
                }
        
        return {
            "success": False,
            "error": "訂單不存在"
        }
    
    def get_all_orders(self):
        """取得所有訂單"""
        return self.orders_data["orders"]
    
    def get_order(self, order_id):
        """取得單一訂單"""
        for order in self.orders_data["orders"]:
            if order["id"] == order_id:
                return order
        return None

# CLI 測試
if __name__ == "__main__":
    import sys
    
    manager = OrderManager()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 order_manager.py add <訂單號> <追蹤號> [物流商] [商品名稱]")
        print("  python3 order_manager.py list")
        print("  python3 order_manager.py remove <ID>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "add" and len(sys.argv) >= 4:
        order_number = sys.argv[2]
        tracking_number = sys.argv[3]
        carrier = sys.argv[4] if len(sys.argv) > 4 else "Unknown"
        product_name = sys.argv[5] if len(sys.argv) > 5 else ""
        
        result = manager.add_order(order_number, tracking_number, carrier, product_name)
        print(result.get("message") or result.get("error"))
    
    elif action == "list":
        orders = manager.get_all_orders()
        print(f"\n📦 訂單列表 ({len(orders)} 筆)\n")
        for order in orders:
            print(f"ID: {order['id']}")
            print(f"訂單號: {order['orderNumber']}")
            print(f"追蹤號: {order['trackingNumber']}")
            print(f"物流商: {order['carrier']}")
            print(f"狀態: {order['status']}")
            print(f"位置: {order['currentLocation']}")
            print("-" * 50)
    
    elif action == "remove" and len(sys.argv) >= 3:
        order_id = int(sys.argv[2])
        result = manager.remove_order(order_id)
        print(result.get("message") or result.get("error"))
    
    else:
        print("❌ 無效的指令")
        sys.exit(1)
