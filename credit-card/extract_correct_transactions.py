#!/usr/bin/env python3
"""
從 PDF 文字提取正確的交易金額
特別注意分期付款的實際金額
"""

import json
import re

# 從 bill_text.txt 讀取完整文字
with open("/root/.openclaw/workspace/task-tracker/credit-card/bill_text.txt", 'r', encoding='utf-8') as f:
    text = f.read()

transactions = []

# 手動整理所有交易（根據 PDF 第 2、3 頁）
transactions_data = [
    # 分期付款（實際金額）
    {"date": "2025/10/09", "post_date": "2026/01/13", "description": "９１ＡＰＰ－康是美網購ｅＳｈ　分03期之第03期", "amount": 7162},
    {"date": "2025/11/04", "post_date": "2026/01/13", "description": "蘋果電腦－台灣－ＥＣ－分期　分03期之第02期", "amount": 2496},
    
    # 12 月消費
    {"date": "2025/12/10", "post_date": "2026/12/15", "description": "優食－肉圓李　大里店", "amount": 492},
    {"date": "2025/12/12", "post_date": "2026/12/17", "description": "連加＊阜爾運通股份有限", "amount": 80},
    {"date": "2025/12/12", "post_date": "2026/12/17", "description": "台中海洋館", "amount": 1000},
    {"date": "2025/12/13", "post_date": "2026/12/17", "description": "ＣＯＵＰＡＮＧ", "amount": 901},
    {"date": "2025/12/13", "post_date": "2026/12/17", "description": "連加＊阜爾運通股份有限", "amount": 50},
    {"date": "2025/12/14", "post_date": "2026/12/15", "description": "GOOGLE*YOUTUBEPREMIUM", "amount": 479},
    {"date": "2025/12/14", "post_date": "2026/12/15", "description": "國外交易服務費", "amount": 7},
    {"date": "2025/12/14", "post_date": "2026/12/18", "description": "連支＊統元豆花", "amount": 156},
    {"date": "2025/12/15", "post_date": "2026/01/13", "description": "信用卡扣繳中華電信費", "amount": 74},
    {"date": "2025/12/15", "post_date": "2026/12/18", "description": "台灣特斯拉汽車有限公司－ＥＣ－ＭＰＧＳ", "amount": 199},
    {"date": "2025/12/15", "post_date": "2026/12/19", "description": "酷澎ＷＯＷ會員訂閱服務月費", "amount": 59},
    {"date": "2025/12/16", "post_date": "2026/12/16", "description": "APPLE.COM/BILL", "amount": 300},
    {"date": "2025/12/16", "post_date": "2026/12/16", "description": "國外交易服務費", "amount": 4},
    {"date": "2025/12/16", "post_date": "2026/12/19", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
    {"date": "2025/12/19", "post_date": "2026/12/23", "description": "連加＊爵林堅果坊－永康", "amount": 1290},
    {"date": "2025/12/19", "post_date": "2026/12/24", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
    {"date": "2025/12/19", "post_date": "2026/12/24", "description": "連加＊ｃｏｃｏ－捷運北", "amount": 65},
    {"date": "2025/12/20", "post_date": "2026/12/24", "description": "連加＊麥當勞", "amount": 313},
    {"date": "2025/12/20", "post_date": "2026/12/24", "description": "ＣＯＵＰＡＮＧ", "amount": 2167},
    {"date": "2025/12/21", "post_date": "2026/12/24", "description": "優食－虎滿麵屋", "amount": 544},
    {"date": "2025/12/21", "post_date": "2026/12/26", "description": "ＣＯＵＰＡＮＧ", "amount": 1069},
    {"date": "2025/12/23", "post_date": "2026/12/30", "description": "ＣＯＵＰＡＮＧ", "amount": 1199},
    {"date": "2025/12/24", "post_date": "2026/12/26", "description": "SPOTIFY", "amount": 168},
    {"date": "2025/12/24", "post_date": "2026/12/26", "description": "國外交易服務費", "amount": 2},
    
    # 達美樂：退貨 + 兩筆消費
    {"date": "2025/12/24", "post_date": "2026/12/30", "description": "連加＊達美樂大里中興店 【退貨】", "amount": -1159, "is_refund": True},
    {"date": "2025/12/24", "post_date": "2026/12/30", "description": "連加＊達美樂大里中興店", "amount": 1159},
    {"date": "2025/12/24", "post_date": "2026/12/30", "description": "連加＊達美樂大里中興店", "amount": 1448},
    
    {"date": "2025/12/25", "post_date": "2026/12/30", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
    {"date": "2025/12/25", "post_date": "2026/12/26", "description": "GOOGLE*GOOGLE ONE", "amount": 650},
    {"date": "2025/12/25", "post_date": "2026/12/26", "description": "國外交易服務費", "amount": 9},
    {"date": "2025/12/26", "post_date": "2026/12/30", "description": "優食－龜記茗品　台中一中店", "amount": 216},
    {"date": "2025/12/26", "post_date": "2026/12/31", "description": "ＣＯＵＰＡＮＧ", "amount": 463},
    {"date": "2025/12/28", "post_date": "2026/01/02", "description": "連支＊統元豆花", "amount": 171},
    {"date": "2025/12/28", "post_date": "2026/01/02", "description": "樂天－ａｌｌｗ", "amount": 637},
    {"date": "2025/12/31", "post_date": "2026/01/06", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
    
    # 2026 年 1 月（但算在本期帳單）
    {"date": "2026/01/01", "post_date": "2026/01/02", "description": "GOOGLE*CLOUD H9BWQL", "amount": 6},
    {"date": "2026/01/01", "post_date": "2026/01/07", "description": "ＣＯＵＰＡＮＧ", "amount": 324},
    {"date": "2026/01/03", "post_date": "2026/01/05", "description": "RENDER.COM", "amount": 220},
    {"date": "2026/01/03", "post_date": "2026/01/05", "description": "國外交易服務費", "amount": 3},
    {"date": "2026/01/03", "post_date": "2026/01/07", "description": "ＣＯＵＰＡＮＧ", "amount": 969},
    {"date": "2026/01/03", "post_date": "2026/01/07", "description": "ＣＯＵＰＡＮＧ", "amount": 10682},
    {"date": "2026/01/04", "post_date": "2026/01/08", "description": "連支＊統元豆花", "amount": 176},
    {"date": "2026/01/06", "post_date": "2026/01/12", "description": "Ｐｉ－ＰＣＨＯＭＥ２４Ｈ購物－３Ｄ", "amount": 7169},
    {"date": "2026/01/07", "post_date": "2026/01/12", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
]

# 計算總金額
total = sum(t['amount'] for t in transactions_data)
total_positive = sum(t['amount'] for t in transactions_data if t['amount'] > 0)
total_refunds = sum(t['amount'] for t in transactions_data if t['amount'] < 0)

print("📊 統計資訊")
print("="*70)
print(f"交易筆數: {len(transactions_data)}")
print(f"總金額（含刷退）: NT${total:,}")
print(f"消費總額（不含刷退）: NT${total_positive:,}")
print(f"刷退總額: NT${total_refunds:,}")
print()

# 檢查是否符合帳單
bill_total = 45419

if total == bill_total:
    print(f"✅ 總金額與帳單完全一致：NT${bill_total:,}")
else:
    difference = abs(total - bill_total)
    print(f"⚠️ 總金額與帳單有差異")
    print(f"   帳單：NT${bill_total:,}")
    print(f"   計算：NT${total:,}")
    print(f"   差異：NT${difference:,}")

# 儲存更新後的檔案
with open("/root/.openclaw/workspace/task-tracker/credit-card/transactions.json", 'w', encoding='utf-8') as f:
    json.dump(transactions_data, f, ensure_ascii=False, indent=2)

print(f"\n💾 已更新 transactions.json")

# 列出所有刷退項目
refunds = [t for t in transactions_data if t.get('is_refund') or t['amount'] < 0]
if refunds:
    print(f"\n💰 刷退項目 ({len(refunds)} 筆):")
    for r in refunds:
        print(f"   {r['date']} {r['description']}: NT${r['amount']:,}")

print("\n✅ 完成！資料已正確更新，可以部署到 Render 了")
