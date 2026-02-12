#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail 連線測試
"""

import imaplib
import email
from email.header import decode_header
import os

def load_credentials():
    """讀取憑證"""
    creds = {}
    with open('.gmail_credentials', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                creds[key] = value
    return creds

def test_connection():
    """測試 Gmail 連線"""
    print("🔐 Gmail 連線測試")
    print("="*60)
    
    try:
        # 讀取憑證
        print("\n📋 步驟 1: 讀取憑證...")
        creds = load_credentials()
        email_address = creds['EMAIL']
        app_password = creds['APP_PASSWORD']
        print(f"   ✅ Email: {email_address}")
        print(f"   ✅ App Password: {app_password[:4]}...{app_password[-4:]}")
        
        # 連接到 Gmail IMAP
        print("\n🌐 步驟 2: 連接到 Gmail IMAP 伺服器...")
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        print("   ✅ 成功連接到 imap.gmail.com")
        
        # 登入
        print("\n🔑 步驟 3: 使用 App Password 登入...")
        mail.login(email_address, app_password)
        print("   ✅ 登入成功！")
        
        # 列出所有資料夾
        print("\n📂 步驟 4: 列出信箱資料夾...")
        status, folders = mail.list()
        print(f"   ✅ 找到 {len(folders)} 個資料夾")
        
        # 選擇收件匣
        print("\n📥 步驟 5: 選擇收件匣...")
        status, messages = mail.select('INBOX')
        total_messages = int(messages[0])
        print(f"   ✅ 收件匣共有 {total_messages} 封信")
        
        # 搜尋 Coupang 相關的信
        print("\n🔍 步驟 6: 搜尋 Coupang 相關郵件...")
        
        # 搜尋條件
        search_criteria = [
            'FROM "coupang"',
            'FROM "tradevan.com.tw"',
            'SUBJECT "Coupang"',
            'SUBJECT "酷澎"'
        ]
        
        found_emails = set()
        for criteria in search_criteria:
            status, data = mail.search(None, criteria)
            if status == 'OK':
                email_ids = data[0].split()
                if email_ids:
                    found_emails.update(email_ids)
                    print(f"   ✅ 條件「{criteria}」找到 {len(email_ids)} 封信")
        
        if found_emails:
            print(f"\n   📊 總共找到 {len(found_emails)} 封 Coupang 相關郵件")
            
            # 顯示最近的一封
            print("\n📧 步驟 7: 讀取最新的一封 Coupang 郵件...")
            latest_id = max(found_emails)
            status, msg_data = mail.fetch(latest_id, '(RFC822)')
            
            if status == 'OK':
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # 解析主旨
                subject = decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # 寄件者
                from_addr = msg.get('From')
                
                # 日期
                date = msg.get('Date')
                
                print(f"   ✅ 主旨：{subject}")
                print(f"   ✅ 寄件者：{from_addr}")
                print(f"   ✅ 日期：{date}")
        else:
            print("\n   ⚠️ 沒有找到 Coupang 相關郵件")
            print("   建議：可能郵件較舊，或還沒有訂單")
        
        # 登出
        mail.logout()
        print("\n✅ 測試完成！Gmail 連線正常！")
        
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"\n❌ IMAP 錯誤：{e}")
        print("\n可能的原因：")
        print("1. App Password 不正確")
        print("2. 兩步驟驗證未開啟")
        print("3. Gmail 安全性設定問題")
        return False
        
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    
    if success:
        print("\n" + "="*60)
        print("🎉 Gmail 連線測試成功！")
        print("="*60)
        print("\n下一步：")
        print("1. ✅ 連線正常")
        print("2. 🔄 開始寫完整的 Email 解析腳本")
        print("3. 📊 設定自動執行")
    else:
        print("\n" + "="*60)
        print("❌ Gmail 連線測試失敗")
        print("="*60)
        print("\n請檢查：")
        print("1. App Password 是否正確")
        print("2. 兩步驟驗證是否已開啟")
        print("3. 是否複製了完整的 App Password")
