#!/usr/bin/env python3
"""
檢查 Linda 信箱中玉山帳單郵件的附件
"""

import imaplib
import email
from email.header import decode_header
import os

EMAIL = "linda.openclaw@gmail.com"
APP_PASSWORD = "sxyrzqjdztsvertn"

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
    print("📧 連接到 Linda 的信箱...\n")
    
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, APP_PASSWORD)
    mail.select("inbox")
    
    # 搜尋包含「玉山」或「信用卡帳單」的郵件
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()
    
    print(f"檢查 {len(email_ids)} 封郵件...\n")
    
    for email_id in reversed(email_ids):
        try:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            
            # 只處理玉山帳單相關的信
            if not any(kw in subject.lower() or kw in from_addr.lower() 
                      for kw in ['玉山', 'esun', '信用卡', '帳單']):
                continue
            
            print(f"📨 主旨: {subject}")
            print(f"   寄件者: {from_addr}")
            print(f"   檢查附件...")
            
            has_attachment = False
            
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = decode_str(filename)
                        print(f"   📎 附件: {filename}")
                        
                        # 儲存附件
                        filepath = f"/root/.openclaw/workspace/task-tracker/credit-card/{filename}"
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        print(f"   💾 已儲存: {filepath}")
                        has_attachment = True
            
            if not has_attachment:
                print(f"   ℹ️ 此郵件沒有附件")
            
            print()
            
        except Exception as e:
            continue
    
    mail.close()
    mail.logout()
    
    print("\n✅ 完成！")

if __name__ == '__main__':
    main()
