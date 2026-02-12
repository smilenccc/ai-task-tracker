#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coupang Email 訂單解析器
自動讀取 Gmail 中的 Coupang 訂單信並記錄
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import json
import re
from datetime import datetime, timedelta
import os

def load_credentials():
    """讀取 Gmail 憑證"""
    creds = {}
    with open('.gmail_credentials', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                creds[key] = value
    return creds

def decode_str(s):
    """解碼郵件字串"""
    if isinstance(s, bytes):
        return s.decode()
    if isinstance(s, str):
        return s
    decoded = decode_header(s)[0]
    if isinstance(decoded[0], bytes):
        return decoded[0].decode(decoded[1] or 'utf-8')
    return decoded[0]

def extract_order_info(email_content, subject, date):
    """從 Email 內容解析訂單資訊"""
    orders = []
    
    # 嘗試解析商品和金額
    # Coupang 訂單信通常包含商品名稱和金額
    
    # 金額模式：NT$ 或 $ 後面跟數字
    amount_patterns = [
        r'NT\$\s*([\d,]+)',
        r'\$\s*([\d,]+)',
        r'總計.*?([\d,]+)',
        r'合計.*?([\d,]+)',
    ]
    
    amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, email_content)
        for match in matches:
            try:
                amount = int(match.replace(',', ''))
                if 10 <= amount <= 1000000:  # 合理的金額範圍
                    amounts.append(amount)
            except:
                pass
    
    # 商品名稱模式
    # 從主旨或內容提取
    product_name = subject
    if '訂單' in product_name:
        # 嘗試從主旨提取商品名
        parts = product_name.split('訂單')
        if len(parts) > 0:
            product_name = parts[0].strip()
    
    # 如果找到金額，建立訂單記錄
    if amounts:
        # 使用最大金額（通常是總金額）
        max_amount = max(amounts)
        
        order = {
            'name': product_name[:100],  # 限制長度
            'amount': max_amount,
            'date': date.strftime('%Y-%m-%d'),
            'store': 'Coupang 酷澎',
            'source': 'email'
        }
        orders.append(order)
    
    return orders

def get_email_body(msg):
    """提取 Email 內容"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
        except:
            pass
    
    return body

def load_purchases():
    """讀取現有購買記錄"""
    if os.path.exists('purchases.json'):
        with open('purchases.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "meta": {
            "createdAt": datetime.now().isoformat(),
            "lastUpdated": datetime.now().isoformat(),
            "currency": "TWD",
            "totalPurchases": 0,
            "totalAmount": 0
        },
        "purchases": []
    }

def save_purchases(data):
    """儲存購買記錄"""
    data['meta']['lastUpdated'] = datetime.now().isoformat()
    data['meta']['totalPurchases'] = len(data['purchases'])
    data['meta']['totalAmount'] = sum(p['amount'] for p in data['purchases'])
    
    with open('purchases.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def order_exists(purchases_data, order_date, amount):
    """檢查訂單是否已存在"""
    for purchase in purchases_data['purchases']:
        if purchase['date'] == order_date and purchase['amount'] == amount:
            return True
    return False

def parse_coupang_emails(days_back=30):
    """解析 Coupang 郵件"""
    print("📧 Coupang Email 訂單解析器")
    print("="*60)
    
    # 讀取憑證
    creds = load_credentials()
    email_address = creds['EMAIL']
    app_password = creds['APP_PASSWORD']
    
    # 連接 Gmail
    print(f"\n🔐 連接到 Gmail: {email_address}")
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(email_address, app_password)
    
    # 選擇收件匣
    mail.select('INBOX')
    
    # 計算搜尋日期
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    
    # 搜尋 Coupang 相關郵件
    print(f"\n🔍 搜尋最近 {days_back} 天的 Coupang 郵件...")
    
    search_criteria = [
        f'(FROM "coupang" SINCE {since_date})',
        f'(FROM "tradevan.com.tw" SINCE {since_date})',
    ]
    
    found_emails = set()
    for criteria in search_criteria:
        status, data = mail.search(None, criteria)
        if status == 'OK':
            email_ids = data[0].split()
            found_emails.update(email_ids)
    
    print(f"   ✅ 找到 {len(found_emails)} 封郵件")
    
    if not found_emails:
        print("\n⚠️ 沒有找到新的 Coupang 郵件")
        mail.logout()
        return []
    
    # 讀取現有記錄
    purchases_data = load_purchases()
    new_orders = []
    
    # 解析每封郵件
    print(f"\n📋 開始解析郵件...")
    for email_id in found_emails:
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 解析主旨
            subject = decode_str(msg['Subject'])
            
            # 解析日期
            date_str = msg.get('Date')
            try:
                email_date = parsedate_to_datetime(date_str)
            except:
                email_date = datetime.now()
            
            # 提取內容
            body = get_email_body(msg)
            
            # 解析訂單資訊
            orders = extract_order_info(body, subject, email_date)
            
            for order in orders:
                # 檢查是否已存在
                if not order_exists(purchases_data, order['date'], order['amount']):
                    # 新增訂單
                    order['id'] = len(purchases_data['purchases']) + len(new_orders) + 1
                    new_orders.append(order)
                    print(f"   📦 新訂單：{order['name'][:50]} - NT$ {order['amount']:,} ({order['date']})")
        
        except Exception as e:
            print(f"   ⚠️ 解析郵件時發生錯誤：{e}")
            continue
    
    # 儲存新訂單
    if new_orders:
        purchases_data['purchases'].extend(new_orders)
        save_purchases(purchases_data)
        print(f"\n✅ 成功新增 {len(new_orders)} 筆訂單記錄")
    else:
        print(f"\n ℹ️ 沒有新的訂單（可能已經記錄過）")
    
    mail.logout()
    return new_orders

if __name__ == "__main__":
    new_orders = parse_coupang_emails(days_back=90)  # 搜尋最近 90 天
    
    if new_orders:
        print("\n" + "="*60)
        print("📊 新增訂單摘要")
        print("="*60)
        for order in new_orders:
            print(f"  • {order['name'][:40]} - NT$ {order['amount']:,}")
        print(f"\n總計：{len(new_orders)} 筆，NT$ {sum(o['amount'] for o in new_orders):,}")
