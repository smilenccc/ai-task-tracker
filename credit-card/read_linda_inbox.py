#!/usr/bin/env python3
"""
讀取 Linda 信箱中的玉山銀行信用卡帳單
"""

import imaplib
import email
from email.header import decode_header
import re

# Linda 的信箱憑證
EMAIL = "linda.openclaw@gmail.com"
APP_PASSWORD = "sxyrzqjdztsvertn"  # 移除空格

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

def get_body(msg):
    """取得郵件內容"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        try:
                            body = part.get_payload(decode=True).decode('big5', errors='ignore')
                        except:
                            pass
                    if body:
                        break
                elif content_type == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        # 簡單移除 HTML 標籤
                        body = re.sub(r'<[^>]+>', '', html)
                    except:
                        pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            try:
                body = msg.get_payload(decode=True).decode('big5', errors='ignore')
            except:
                body = str(msg.get_payload())
    
    return body

def main():
    print("📧 連接到 Linda 的信箱 (linda.openclaw@gmail.com)...\n")
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, APP_PASSWORD)
        mail.select("inbox")
        
        # 搜尋所有郵件
        status, messages = mail.search(None, 'ALL')
        
        if status != "OK":
            print("❌ 搜尋失敗")
            return
        
        email_ids = messages[0].split()
        total = len(email_ids)
        
        print(f"📬 收件匣共有 {total} 封郵件\n")
        print("="*70 + "\n")
        
        # 列出所有郵件
        for idx, email_id in enumerate(reversed(email_ids), 1):
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = decode_str(msg["Subject"])
                from_addr = decode_str(msg["From"])
                date = decode_str(msg["Date"])
                
                print(f"📨 郵件 #{idx}")
                print(f"   主旨: {subject}")
                print(f"   寄件者: {from_addr}")
                print(f"   日期: {date}")
                
                # 如果是玉山銀行的信，提取完整內容
                if any(keyword in from_addr.lower() or keyword in subject.lower() 
                      for keyword in ['玉山', 'esun', 'e.sun', '信用卡', '帳單']):
                    
                    body = get_body(msg)
                    
                    # 儲存完整內容
                    output_file = f"/root/.openclaw/workspace/task-tracker/credit-card/esun_bill_{idx}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(f"主旨: {subject}\n")
                        f.write(f"日期: {date}\n")
                        f.write(f"寄件者: {from_addr}\n")
                        f.write("="*70 + "\n\n")
                        f.write(body)
                    
                    print(f"   💾 已儲存完整內容: {output_file}")
                    
                    # 尋找重要資訊
                    print(f"\n   📊 分析帳單內容:")
                    
                    # 尋找總金額
                    total_match = re.search(r'本期應繳總額.*?[\$NT]?\s*(\d{1,3}(?:,\d{3})*)', body)
                    if total_match:
                        print(f"      💵 本期應繳總額: NT${total_match.group(1)}")
                    
                    # 尋找刷退
                    refund_lines = [line for line in body.split('\n') 
                                   if any(kw in line for kw in ['刷退', '退款', '取消', 'REFUND', '折讓', '-$'])]
                    
                    if refund_lines:
                        print(f"      ⚠️ 發現 {len(refund_lines)} 筆可能的刷退:")
                        for line in refund_lines[:5]:  # 只顯示前 5 筆
                            print(f"         • {line.strip()[:80]}")
                    
                    print()
                
                print()
                
            except Exception as e:
                print(f"❌ 處理郵件 #{idx} 時發生錯誤: {e}\n")
                continue
        
        mail.close()
        mail.logout()
        
        print("\n✅ 完成！請檢查儲存的檔案")
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")

if __name__ == '__main__':
    main()
