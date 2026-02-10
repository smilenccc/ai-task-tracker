#!/usr/bin/env python3
"""
ECMS Express 追蹤工具
"""

import sys
import json
from datetime import datetime

def track_ecms_express(tracking_number):
    """追蹤 ECMS Express 包裹"""
    print(f"\n📦 ECMS Express 包裹追蹤")
    print(f"📋 追蹤號: {tracking_number}")
    print(f"🕐 查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # ECMS Express 追蹤連結
    # 注意：ECMS Express 通常透過 Amazon 整合追蹤
    urls = {
        'amazon': f"https://track.amazon.de/{tracking_number}",
        'ecms_cn': f"http://www.ecmsglobal.com/track?number={tracking_number}",
        'order': f"https://www.amazon.de/gp/css/shiptrack/view.html?orderID=303-0977485-2042700"
    }
    
    print("🔗 追蹤連結選項：")
    print(f"   Amazon 追蹤: {urls['amazon']}")
    print(f"   ECMS 官網: {urls['ecms_cn']}")
    print(f"   訂單頁面: {urls['order']}")
    
    # 讀取目前狀態
    try:
        with open('/root/.openclaw/workspace/amazon-tracker/package_status.json', 'r') as f:
            status = json.load(f)
        
        print("\n📍 目前狀態：")
        print(f"   狀態: {status['current_status']}")
        print(f"   詳情: {status['status_detail']}")
        print(f"   更新時間: {status['last_updated']}")
        
        print("\n🏠 收件地址：")
        print(f"   {status['delivery_address']['name']}")
        print(f"   {status['delivery_address']['address']}")
        
    except FileNotFoundError:
        print("\n⚠️ 狀態檔案不存在")
    
    print("\n💡 ECMS Express 是 Amazon 合作的國際物流商")
    print("   專門處理從德國到亞洲的跨境包裹")

if __name__ == '__main__':
    tracking_number = sys.argv[1] if len(sys.argv) > 1 else "AXIXPPL001333550"
    track_ecms_express(tracking_number)
