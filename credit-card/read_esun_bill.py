#!/usr/bin/env python3
"""
讀取玉山銀行信用卡帳單郵件
找出所有交易項目（包括刷退）
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime

# Gmail 憑證
EMAIL = "smilenctu@gmail.com"
APP_PASSWORD = "uiakfrabqxgqlbsb"

def connect_gmail():
    """連接到 Gmail"""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, APP_PASSWORD)
    return mail

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
                            body = str(part.get_payload())
                    if body:
                        break
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            try:
                body = msg.get_payload(decode=True).decode('big5', errors='ignore')
            except:
                body = str(msg.get_payload())
    
    return body

def search_credit_card_bills():
    """搜尋信用卡帳單"""
    mail = connect_gmail()
    
    # 選擇收件匣
    mail.select("inbox")
    
    # 搜尋玉山銀行的郵件（2025年12月到2026年1月）
    # 搜尋關鍵字：玉山、E.SUN、信用卡、帳單
    queries = [
        '(FROM "玉山" SINCE 01-Dec-2025)',
        '(FROM "esun" SINCE 01-Dec-2025)',
        '(FROM "e.sun" SINCE 01-Dec-2025)',
        '(SUBJECT "信用卡" SINCE 01-Dec-2025)',
        '(SUBJECT "帳單" SINCE 01-Dec-2025)',
    ]
    
    all_emails = set()
    
    for query in queries:
        try:
            status, messages = mail.search(None, query)
            if status == "OK":
                email_ids = messages[0].split()
                all_emails.update(email_ids)
        except:
            continue
    
    print(f"📧 找到 {len(all_emails)} 封相關郵件\n")
    
    bills = []
    
    for email_id in sorted(all_emails, reverse=True)[:10]:  # 只看最新 10 封
        try:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            date = decode_str(msg["Date"])
            
            # 只處理玉山銀行的信
            if not any(keyword in from_addr.lower() or keyword in subject.lower() 
                      for keyword in ['玉山', 'esun', 'e.sun', '信用卡帳單']):
                continue
            
            body = get_body(msg)
            
            print(f"📨 主旨: {subject}")
            print(f"   寄件者: {from_addr}")
            print(f"   日期: {date}")
            print(f"   內容長度: {len(body)} 字元")
            print()
            
            bills.append({
                'subject': subject,
                'from': from_addr,
                'date': date,
                'body': body
            })
            
        except Exception as e:
            print(f"❌ 處理郵件時發生錯誤: {e}")
            continue
    
    mail.close()
    mail.logout()
    
    return bills

def extract_transactions(body):
    """提取交易明細"""
    lines = body.split('\n')
    
    transactions = []
    refunds = []
    
    # 尋找交易明細區塊
    in_transaction_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 偵測交易明細開始
        if any(keyword in line for keyword in ['國內一般消費', '本期新增交易', '消費明細', '交易日期']):
            in_transaction_section = True
            continue
        
        # 偵測交易明細結束
        if in_transaction_section and any(keyword in line for keyword in ['本期應繳總額', '最低應繳金額', '繳款期限']):
            break
        
        if in_transaction_section and line:
            # 尋找金額（正負數都要）
            amount_match = re.search(r'(-?\$?\d{1,3}(,\d{3})*)', line)
            
            if amount_match:
                # 檢查是否為刷退
                is_refund = '-' in amount_match.group(1) or any(keyword in line for keyword in ['刷退', '退款', '取消', 'REFUND', '折讓'])
                
                if is_refund:
                    refunds.append(line)
                    print(f"💰 刷退: {line}")
                else:
                    transactions.append(line)
    
    return transactions, refunds

def main():
    print("🔍 讀取玉山銀行信用卡帳單...\n")
    print("="*70 + "\n")
    
    bills = search_credit_card_bills()
    
    if not bills:
        print("❌ 找不到帳單郵件")
        return
    
    print("\n" + "="*70)
    print("📊 分析帳單內容")
    print("="*70 + "\n")
    
    for idx, bill in enumerate(bills):
        print(f"\n📧 帳單 #{idx+1}: {bill['subject']}")
        print(f"   日期: {bill['date']}")
        print("-"*70)
        
        # 儲存完整內容
        output_file = f"/root/.openclaw/workspace/task-tracker/credit-card/bill_{idx+1}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"主旨: {bill['subject']}\n")
            f.write(f"日期: {bill['date']}\n")
            f.write(f"寄件者: {bill['from']}\n")
            f.write("="*70 + "\n\n")
            f.write(bill['body'])
        
        print(f"   💾 已儲存: {output_file}")
        
        # 提取交易
        transactions, refunds = extract_transactions(bill['body'])
        
        print(f"\n   📝 一般交易: {len(transactions)} 筆")
        print(f"   💰 刷退交易: {len(refunds)} 筆")
        
        if refunds:
            print(f"\n   ⚠️ 刷退明細:")
            for r in refunds:
                print(f"      {r}")
        
        # 尋找總金額
        total_match = re.search(r'本期應繳總額.*?(\d{1,3}(,\d{3})*)', bill['body'])
        if total_match:
            print(f"\n   💵 本期應繳總額: NT${total_match.group(1)}")

if __name__ == '__main__':
    main()
