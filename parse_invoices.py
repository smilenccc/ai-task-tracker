#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 Coupang 電子發票郵件（真正的訂單）
"""

import imaplib
import email
from email.header import decode_header
import re
import json
from datetime import datetime

def load_credentials():
    creds = {}
    with open('.gmail_credentials', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                creds[key] = value
    return creds

def decode_mime_header(header):
    if not header:
        return ""
    try:
        decoded_parts = decode_header(header)
        result = ''
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                result += content.decode(encoding or 'utf-8', errors='ignore')
            else:
                result += str(content)
        return re.sub(r'\s+', ' ', result).strip()
    except:
        return header

def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/plain", "text/html"]:
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

# 連接
print("📧 解析 Coupang 電子發票郵件")
print("="*60)

creds = load_credentials()
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login(creds['EMAIL'], creds['APP_PASSWORD'])
mail.select('INBOX')

# 搜尋電子發票
status, data = mail.search(None, 'FROM "coupang" SUBJECT "發票"')
if status == 'OK' and data[0]:
    email_ids = data[0].split()
    print(f"\n✅ 找到 {len(email_ids)} 封電子發票郵件\n")
    
    invoices = []
    
    for i, email_id in enumerate(email_ids):
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_mime_header(msg['Subject'])
            date = msg.get('Date')
            body = get_email_body(msg)
            
            # 提取金額
            amount_patterns = [
                r'總金額[：:]\s*NT?\$?\s*([\d,]+)',
                r'合計[：:]\s*NT?\$?\s*([\d,]+)',
                r'應付金額[：:]\s*NT?\$?\s*([\d,]+)',
                r'NT\$\s*([\d,]+)',
            ]
            
            amounts = []
            for pattern in amount_patterns:
                matches = re.findall(pattern, body)
                for match in matches:
                    try:
                        amount = int(match.replace(',', ''))
                        if 10 <= amount <= 1000000:
                            amounts.append(amount)
                    except:
                        pass
            
            # 提取商品名稱（簡化版）
            product_patterns = [
                r'商品名稱[：:](.*?)(?:\n|$)',
                r'品名[：:](.*?)(?:\n|$)',
            ]
            
            product_name = "Coupang 購物"
            for pattern in product_patterns:
                matches = re.findall(pattern, body)
                if matches:
                    product_name = matches[0].strip()[:50]
                    break
            
            if amounts:
                invoice = {
                    'id': i + 1,
                    'name': product_name,
                    'amount': max(amounts),
                    'date': date[:16] if date else '',
                    'subject': subject
                }
                invoices.append(invoice)
                print(f"{i+1}. {invoice['name'][:40]:40} NT$ {invoice['amount']:,} ({invoice['date']})")
        
        except Exception as e:
            print(f"⚠️ 解析第 {i+1} 封時發生錯誤：{e}")
            continue
    
    print(f"\n📊 總計：{len(invoices)} 筆發票")
    print(f"💰 總金額：NT$ {sum(inv['amount'] for inv in invoices):,}")
    
    # 儲存
    with open('invoices_found.json', 'w', encoding='utf-8') as f:
        json.dump(invoices, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已儲存到 invoices_found.json")

mail.logout()
