#!/usr/bin/env python3
"""
檢查 Gmail 中的玉山信用卡帳單郵件
特別注意刷退項目
"""

import os
import sys
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from datetime import datetime
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """取得 Gmail API 服務"""
    creds = None
    token_path = '/root/.openclaw/workspace/.gmail-token.pickle'
    creds_path = '/root/.openclaw/workspace/.gmail-credentials.json'
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print("❌ 找不到 Gmail credentials 檔案")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def search_credit_card_bills(service):
    """搜尋信用卡帳單郵件"""
    try:
        # 搜尋玉山信用卡帳單（2025年12月）
        query = 'from:玉山銀行 OR from:esun OR subject:信用卡 after:2025/12/01 before:2026/01/31'
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=20
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("❌ 找不到信用卡帳單郵件")
            return []
        
        print(f"📧 找到 {len(messages)} 封郵件\n")
        
        bills = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            
            # 取得郵件內容
            body = get_message_body(msg_data['payload'])
            
            bills.append({
                'id': msg['id'],
                'subject': subject,
                'date': date,
                'from': from_email,
                'body': body[:2000]  # 只取前 2000 字元
            })
            
            print(f"📨 主旨: {subject}")
            print(f"   日期: {date}")
            print(f"   寄件者: {from_email}")
            print()
        
        return bills
        
    except HttpError as error:
        print(f'❌ 發生錯誤: {error}')
        return []

def get_message_body(payload):
    """取得郵件內容"""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    
    return body

def extract_transactions_from_bill(body):
    """從帳單內容提取交易資料（包括刷退）"""
    transactions = []
    
    # 找出所有交易紀錄
    # 格式通常是：日期 商家名稱 金額
    lines = body.split('\n')
    
    for line in lines:
        # 尋找金額模式（可能是負數代表刷退）
        if re.search(r'\d{1,3}(,\d{3})*', line):
            # 檢查是否包含「刷退」、「退款」等關鍵字
            is_refund = any(keyword in line for keyword in ['刷退', '退款', '退貨', '取消', 'REFUND'])
            
            if is_refund:
                print(f"🔍 發現可能的刷退: {line.strip()}")
                transactions.append({
                    'type': 'refund',
                    'content': line.strip()
                })
    
    return transactions

def main():
    print("🔍 檢查玉山信用卡帳單郵件...\n")
    
    service = get_gmail_service()
    if not service:
        return
    
    bills = search_credit_card_bills(service)
    
    if not bills:
        return
    
    print("\n" + "="*60)
    print("📊 分析帳單內容（尋找刷退項目）")
    print("="*60 + "\n")
    
    for bill in bills:
        print(f"\n📧 帳單: {bill['subject']}")
        print(f"   日期: {bill['date']}")
        print("-" * 60)
        
        transactions = extract_transactions_from_bill(bill['body'])
        
        if transactions:
            print(f"\n⚠️ 發現 {len(transactions)} 筆可能的刷退:")
            for t in transactions:
                print(f"   - {t['content']}")
        else:
            print("   ℹ️ 未發現明顯的刷退項目")
        
        # 儲存完整郵件內容供檢視
        output_file = f"/root/.openclaw/workspace/task-tracker/credit-card/bill_{bill['id'][:8]}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"主旨: {bill['subject']}\n")
            f.write(f"日期: {bill['date']}\n")
            f.write(f"寄件者: {bill['from']}\n")
            f.write("="*60 + "\n\n")
            f.write(bill['body'])
        
        print(f"   💾 完整內容已儲存: {output_file}")

if __name__ == '__main__':
    main()
