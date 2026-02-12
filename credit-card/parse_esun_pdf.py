#!/usr/bin/env python3
"""
解析玉山銀行信用卡帳單 PDF
提取所有交易明細（包括刷退）
"""

import pdfplumber
import re
import json

PDF_PATH = "/root/.openclaw/workspace/task-tracker/credit-card/ESUN_Estatement_11412.pdf"

def parse_bill():
    """解析帳單 PDF"""
    
    print("📄 開啟 PDF 檔案...\n")
    
    with pdfplumber.open(PDF_PATH) as pdf:
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
        
        for line in lines:
            # 尋找包含金額的行（可能是正數或負數）
            # 金額格式：1,234 或 -1,234 或 $1,234
            if re.search(r'\d{1,3}(?:,\d{3})*', line):
                
                # 檢查是否為刷退（包含負號或「刷退」關鍵字）
                is_refund = (
                    re.search(r'-\s*\$?\d{1,3}(?:,\d{3})*', line) or
                    any(kw in line for kw in ['刷退', '退款', '取消', 'REFUND', '折讓'])
                )
                
                if is_refund:
                    refunds.append(line.strip())
                    print(f"💰 刷退: {line.strip()}")
                elif any(kw in line for kw in ['應繳總額', '最低', '前期', '本期']):
                    # 跳過統計行
                    continue
                else:
                    transactions.append(line.strip())
        
        print(f"\n📝 一般交易: {len(transactions)} 筆")
        print(f"💰 刷退交易: {len(refunds)} 筆")
        
        # 尋找總金額
        total_match = re.search(r'本期應繳總額.*?[\$NT]?\s*(\d{1,3}(?:,\d{3})*)', all_text, re.IGNORECASE)
        if total_match:
            total = total_match.group(1)
            print(f"\n💵 本期應繳總額: NT${total}")
        
        # 儲存結果
        result = {
            'total_amount': total if total_match else 'unknown',
            'transactions': transactions,
            'refunds': refunds
        }
        
        with open("/root/.openclaw/workspace/task-tracker/credit-card/parsed_bill.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 解析結果已儲存: parsed_bill.json")

if __name__ == '__main__':
    parse_bill()
