#!/usr/bin/env python3
"""
列出最近的所有郵件
"""

import imaplib
import email
from email.header import decode_header

EMAIL = "smilenctu@gmail.com"
APP_PASSWORD = "uiakfrabqxgqlbsb"

def decode_str(s):
    """解碼郵件標題"""
    if s is None:
        return ""
    decoded = decode_header(s)
    result = []
    for content, encoding in decoded:
        if isinstance(content, bytes):
            try:
                result.append(content.decode(encoding or 'utf-8', errors='ignore'))
            except:
                result.append(content.decode('utf-8', errors='ignore'))
        else:
            result.append(str(content))
    return ''.join(result)

def main():
    print("📧 連接到 Gmail...\n")
    
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, APP_PASSWORD)
    mail.select("inbox")
    
    # 搜尋最近的郵件
    status, messages = mail.search(None, 'ALL')
    
    if status != "OK":
        print("❌ 搜尋失敗")
        return
    
    email_ids = messages[0].split()
    total = len(email_ids)
    
    print(f"📬 收件匣共有 {total} 封郵件\n")
    print("最近 20 封郵件:")
    print("="*70 + "\n")
    
    # 只看最新 20 封
    for email_id in reversed(email_ids[-20:]):
        try:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            date = decode_str(msg["Date"])
            
            print(f"📨 主旨: {subject[:60]}")
            print(f"   寄件者: {from_addr[:60]}")
            print(f"   日期: {date}")
            print()
            
        except Exception as e:
            continue
    
    mail.close()
    mail.logout()

if __name__ == '__main__':
    main()
