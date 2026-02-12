#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from email.header import decode_header
import re

def decode_mime_header(header):
    """完整解碼 MIME 編碼的標頭"""
    if not header:
        return ""
    
    try:
        decoded_parts = decode_header(header)
        result = ''
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                # 嘗試用指定編碼解碼
                try:
                    result += content.decode(encoding or 'utf-8', errors='ignore')
                except:
                    result += content.decode('utf-8', errors='ignore')
            else:
                result += str(content)
        
        # 移除多餘的空白和換行
        result = re.sub(r'\s+', ' ', result).strip()
        return result[:100]  # 限制長度
    except:
        return header[:100]

# 讀取資料
with open('purchases.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 重新解碼所有商品名稱
print("🔧 修正商品名稱編碼...")
for purchase in data['purchases']:
    original = purchase['name']
    decoded = decode_mime_header(original)
    purchase['name'] = decoded
    if original != decoded:
        print(f"  ✅ {decoded[:50]}")

# 儲存
with open('purchases.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 完成！共處理 {len(data['purchases'])} 筆記錄")
