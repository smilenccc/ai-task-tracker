#!/usr/bin/env python3
"""
解析玉山銀行信用卡帳單 PDF（需要密碼）
提取所有交易明細（包括刷退）
"""

import pdfplumber
import re
import json

PDF_PATH = "/root/.openclaw/workspace/task-tracker/credit-card/ESUN_Estatement_11412.pdf"
PASSWORD = "K121715079"

def parse_bill():
    """解析帳單 PDF"""
    
    print("📄 開啟 PDF 檔案（使用密碼）...\n")
    
    try:
        with pdfplumber.open(PDF_PATH, password=PASSWORD) as pdf:
            print(f"✅ PDF 解鎖成功！")
            print(f"📊 PDF 總頁數: {len(pdf.pages)}\n")
            print("="*70 + "\n")
            
            all_text = ""
            
            for i, page in enumerate(pdf.pages, 1):
                print(f"📄 第 {i} 頁:")
                text = page.extract_text()
                all_text += text + "\n"
                print(text)
                print("\n" + "-"*70 + "\n")
            
            # 儲存完整文字
            with open("/root/.openclaw/workspace/task-tracker/credit-card/bill_text.txt", 'w', encoding='utf-8') as f:
                f.write(all_text)
            
            print("\n💾 完整文字已儲存: bill_text.txt")
            
            # 提取交易明細
            print("\n" + "="*70)
            print("📊 分析交易明細")
            print("="*70 + "\n")
            
            transactions = []
            refunds = []
            
            lines = all_text.split('\n')
            
            in_transaction_section = False
            
            for line in lines:
                line_strip = line.strip()
                
                # 偵測交易明細區塊開始
                if any(kw in line_strip for kw in ['交易日期', '消費明細', '國內一般消費', '本期新增交易']):
                    in_transaction_section = True
                    continue
                
                # 偵測交易明細區塊結束
                if in_transaction_section and any(kw in line_strip for kw in ['本期應繳總額', '最低應繳金額', '前期結欠']):
                    in_transaction_section = False
                
                if not in_transaction_section:
                    continue
                
                # 尋找包含金額的行
                if re.search(r'\d{1,3}(?:,\d{3})*', line_strip):
                    
                    # 檢查是否為刷退（包含負號或「刷退」關鍵字）
                    is_refund = (
                        re.search(r'-\s*\$?\d{1,3}(?:,\d{3})*', line_strip) or
                        any(kw in line_strip for kw in ['刷退', '退款', '取消', 'REFUND', '折讓', '(-'])
                    )
                    
                    if is_refund:
                        refunds.append(line_strip)
                        print(f"💰 刷退: {line_strip}")
                    else:
                        transactions.append(line_strip)
            
            print(f"\n📝 一般交易: {len(transactions)} 筆")
            print(f"💰 刷退交易: {len(refunds)} 筆")
            
            # 尋找總金額
            total_match = re.search(r'本期應繳總額.*?[\$NT]?\s*(\d{1,3}(?:,\d{3})*)', all_text, re.IGNORECASE | re.MULTILINE)
            total_amount = total_match.group(1) if total_match else 'unknown'
            
            if total_match:
                print(f"\n💵 本期應繳總額: NT${total_amount}")
            
            # 儲存結果
            result = {
                'total_amount': total_amount,
                'transactions_count': len(transactions),
                'refunds_count': len(refunds),
                'transactions': transactions,
                'refunds': refunds
            }
            
            with open("/root/.openclaw/workspace/task-tracker/credit-card/parsed_bill.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 解析結果已儲存: parsed_bill.json")
            
            return result
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return None

if __name__ == '__main__':
    parse_bill()
