#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尋找真正的 Coupang 訂單確認信
"""

import imaplib
import email
from email.header import decode_header
import re

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

# 連接 Gmail
creds = load_credentials()
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login(creds['EMAIL'], creds['APP_PASSWORD'])
mail.select('INBOX')

# 搜尋包含「訂單」的 Coupang 郵件
print("🔍 尋找真正的訂單確認信...\n")

search_terms = [
    '(FROM "coupang" SUBJECT "訂單")',
    '(FROM "tradevan.com.tw" SUBJECT "訂單")',
    '(FROM "coupang" SUBJECT "購買")',
    '(FROM "tradevan.com.tw" SUBJECT "確認")',
]

found_orders = {}

for term in search_terms:
    try:
        status, data = mail.search(None, term.encode('utf-8'))
        if status == 'OK' and data[0]:
            email_ids = data[0].split()
            print(f"✅ 搜尋條件「{term}」找到 {len(email_ids)} 封")
            
            # 顯示最近 3 封的主旨
            for email_id in email_ids[-3:]:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    subject = decode_mime_header(msg['Subject'])
                    from_addr = msg.get('From')
                    date = msg.get('Date')
                    
                    print(f"\n📧 {email_id.decode()}")
                    print(f"   主旨：{subject}")
                    print(f"   寄件者：{from_addr}")
                    print(f"   日期：{date}")
    except Exception as e:
        print(f"❌ 搜尋失敗：{e}")

mail.logout()
