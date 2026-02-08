#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
購物記錄新增工具
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def add_purchase(name, amount, store="Coupang 酷澎", category=None, order_id=None, date=None):
    """新增購物記錄"""
    
    # 讀取現有資料
    purchases_file = Path(__file__).parent / "purchases.json"
    
    with open(purchases_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 建立新記錄
    purchase = {
        "id": len(data["purchases"]) + 1,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "name": name,
        "amount": int(amount),
        "store": store,
    }
    
    if category:
        purchase["category"] = category
    if order_id:
        purchase["orderId"] = order_id
    
    # 新增記錄
    data["purchases"].append(purchase)
    
    # 更新統計
    data["meta"]["lastUpdated"] = datetime.now().isoformat()
    data["meta"]["totalPurchases"] = len(data["purchases"])
    data["meta"]["totalAmount"] = sum(p["amount"] for p in data["purchases"])
    
    # 儲存
    with open(purchases_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已記錄購買：{name} - NT$ {purchase['amount']:,}")
    print(f"📊 總消費：NT$ {data['meta']['totalAmount']:,} ({data['meta']['totalPurchases']} 筆)")
    
    return purchase

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方式: python3 add_purchase.py <商品名稱> <金額> [商店] [分類] [訂單編號]")
        print("範例: python3 add_purchase.py 'Nintendo Switch' 13850 'Coupang 酷澎' '3C電子'")
        sys.exit(1)
    
    name = sys.argv[1]
    amount = sys.argv[2]
    store = sys.argv[3] if len(sys.argv) > 3 else "Coupang 酷澎"
    category = sys.argv[4] if len(sys.argv) > 4 else None
    order_id = sys.argv[5] if len(sys.argv) > 5 else None
    
    add_purchase(name, amount, store, category, order_id)
