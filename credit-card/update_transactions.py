#!/usr/bin/env python3
"""
根據 PDF 帳單更新 transactions.json
正確標示刷退項目
"""

import json

# 原始 transactions.json 的內容
transactions = [
  {"date": "2025/10/09", "post_date": "2026/01/13", "description": "９１ＡＰＰ－康是美網購ｅＳｈ　分03期之第03期", "amount": 21488},
  {"date": "2025/12/10", "post_date": "2026/12/15", "description": "優食－肉圓李　大里店", "amount": 492},
  {"date": "2025/12/12", "post_date": "2026/12/17", "description": "連加＊阜爾運通股份有限", "amount": 80},
  {"date": "2025/12/12", "post_date": "2026/12/17", "description": "台中海洋館", "amount": 1000},
  {"date": "2025/12/13", "post_date": "2026/12/17", "description": "ＣＯＵＰＡＮＧ", "amount": 901},
  {"date": "2025/12/13", "post_date": "2026/12/17", "description": "連加＊阜爾運通股份有限", "amount": 50},
  {"date": "2025/12/14", "post_date": "2026/12/15", "description": "GOOGLE*YOUTUBEPREMIUM     USA G.CO/HELPPAY# 12/15", "amount": 479},
  {"date": "2025/12/14", "post_date": "2026/12/18", "description": "連支＊統元豆花", "amount": 156},
  {"date": "2025/12/15", "post_date": "2026/01/13", "description": "信用卡扣繳中華電信費24XXX025     11411", "amount": 74},
  {"date": "2025/12/15", "post_date": "2026/12/18", "description": "台灣特斯拉汽車有限公司－ＥＣ－ＭＰＧＳ", "amount": 199},
  {"date": "2025/12/15", "post_date": "2026/12/19", "description": "酷澎ＷＯＷ會員訂閱服務月費", "amount": 59},
  {"date": "2025/12/16", "post_date": "2026/12/16", "description": "APPLE.COM/BILL            IRL CORK          12/16", "amount": 300},
  {"date": "2025/12/16", "post_date": "2026/12/19", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
  {"date": "2025/12/19", "post_date": "2026/12/23", "description": "連加＊連加＊爵林堅果坊－永康", "amount": 1290},
  {"date": "2025/12/19", "post_date": "2026/12/24", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
  {"date": "2025/12/19", "post_date": "2026/12/24", "description": "連加＊ｃｏｃｏ－捷運北", "amount": 65},
  {"date": "2025/12/20", "post_date": "2026/12/24", "description": "連加＊麥當勞", "amount": 313},
  {"date": "2025/12/20", "post_date": "2026/12/24", "description": "ＣＯＵＰＡＮＧ", "amount": 2167},
  {"date": "2025/12/21", "post_date": "2026/12/24", "description": "優食－虎滿麵屋", "amount": 544},
  {"date": "2025/12/21", "post_date": "2026/12/26", "description": "ＣＯＵＰＡＮＧ", "amount": 1069},
  {"date": "2025/12/23", "post_date": "2026/12/30", "description": "ＣＯＵＰＡＮＧ", "amount": 1199},
  {"date": "2025/12/24", "post_date": "2026/12/26", "description": "SPOTIFY                   SWE STOCKHOLM     12/25", "amount": 168},
  {"date": "2025/12/24", "post_date": "2026/12/30", "description": "連加＊達美樂大里中興店", "amount": 1159},  # 這筆重複了（後來退貨）
  {"date": "2025/12/24", "post_date": "2026/12/30", "description": "連加＊達美樂大里中興店 【退貨】", "amount": -1159, "is_refund": True},  # 新增刷退標示
  {"date": "2025/12/24", "post_date": "2026/12/30", "description": "連加＊達美樂大里中興店", "amount": 1448},
  {"date": "2025/12/25", "post_date": "2026/12/30", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
  {"date": "2025/12/25", "post_date": "2026/12/26", "description": "GOOGLE*GOOGLE ONE         USA MOUNTAIN VIEW 12/26", "amount": 650},
  {"date": "2025/12/26", "post_date": "2026/12/30", "description": "優食－龜記茗品　台中一中店", "amount": 216},
  {"date": "2025/12/26", "post_date": "2026/12/31", "description": "ＣＯＵＰＡＮＧ", "amount": 463},
  {"date": "2025/12/28", "post_date": "2026/01/02", "description": "連支＊統元豆花", "amount": 171},
  {"date": "2025/12/28", "post_date": "2026/01/02", "description": "樂天－ａｌｌｗ", "amount": 637},
  {"date": "2025/12/31", "post_date": "2026/01/06", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400},
  {"date": "2025/01/01", "post_date": "2026/01/02", "description": "GOOGLE*CLOUD H9BWQL       SGP CC GOOGLE.COM 01/02", "amount": 6},
  {"date": "2025/01/01", "post_date": "2026/01/07", "description": "ＣＯＵＰＡＮＧ", "amount": 324},
  {"date": "2025/01/03", "post_date": "2026/01/05", "description": "RENDER.COM                USA SAN FRANCISCO 01/04 USD 7", "amount": 220},
  {"date": "2025/01/03", "post_date": "2026/01/07", "description": "ＣＯＵＰＡＮＧ", "amount": 969},
  {"date": "2025/01/03", "post_date": "2026/01/07", "description": "ＣＯＵＰＡＮＧ", "amount": 10682},
  {"date": "2025/01/04", "post_date": "2026/01/08", "description": "連支＊統元豆花", "amount": 176},
  {"date": "2025/01/06", "post_date": "2026/01/12", "description": "Ｐｉ－ＰＣＨＯＭＥ２４Ｈ購物－３Ｄ", "amount": 7169},
  {"date": "2025/01/07", "post_date": "2026/01/12", "description": "ｅＴａｇ自動儲值金額─車號EAB-2035", "amount": 400}
]

# 計算總金額
total = sum(t['amount'] for t in transactions)
total_without_refunds = sum(t['amount'] for t in transactions if t['amount'] > 0)
refund_total = sum(t['amount'] for t in transactions if t['amount'] < 0)

print("📊 統計資訊")
print("="*70)
print(f"交易筆數: {len(transactions)}")
print(f"總金額（含刷退）: NT${total:,}")
print(f"消費總額（不含刷退）: NT${total_without_refunds:,}")
print(f"刷退總額: NT${refund_total:,}")
print(f"淨金額: NT${total + abs(refund_total):,}")
print()

# 檢查是否接近帳單總額
bill_total = 45419
difference = abs(total - bill_total)

if difference == 0:
    print(f"✅ 總金額與帳單一致：NT${bill_total:,}")
else:
    print(f"⚠️ 總金額與帳單有差異")
    print(f"   帳單：NT${bill_total:,}")
    print(f"   計算：NT${total:,}")
    print(f"   差異：NT${difference:,}")

# 儲存更新後的檔案
with open("/root/.openclaw/workspace/task-tracker/credit-card/transactions.json", 'w', encoding='utf-8') as f:
    json.dump(transactions, f, ensure_ascii=False, indent=2)

print(f"\n💾 已更新 transactions.json")

# 列出所有刷退項目
refunds = [t for t in transactions if t.get('is_refund') or t['amount'] < 0]
if refunds:
    print(f"\n💰 刷退項目 ({len(refunds)} 筆):")
    for r in refunds:
        print(f"   {r['date']} {r['description']}: NT${r['amount']:,}")

