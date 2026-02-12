#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coupang 自動登入測試腳本
測試技術可行性，不需要真實帳密
"""

import requests
from bs4 import BeautifulSoup
import json

def test_coupang_access():
    """測試能否訪問 Coupang 網站"""
    print("🔍 測試 1: 訪問 Coupang 首頁...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get('https://www.coupang.com', headers=headers, timeout=10)
        print(f"✅ 首頁訪問成功！狀態碼：{response.status_code}")
        return True
    except Exception as e:
        print(f"❌ 訪問失敗：{e}")
        return False

def test_tw_coupang():
    """測試台灣 Coupang 網站"""
    print("\n🔍 測試 2: 訪問台灣 Coupang...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get('https://tw.coupang.com', headers=headers, timeout=10)
        print(f"✅ 台灣站訪問成功！狀態碼：{response.status_code}")
        
        # 檢查是否有登入相關元素
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找登入相關的連結或按鈕
        login_elements = soup.find_all(['a', 'button'], string=lambda text: text and ('登入' in text or '登录' in text or 'login' in text.lower()))
        
        if login_elements:
            print(f"✅ 找到 {len(login_elements)} 個登入相關元素")
            for elem in login_elements[:3]:
                print(f"   - {elem.get('href', 'N/A')} : {elem.get_text(strip=True)}")
        else:
            print("⚠️ 未找到明顯的登入元素")
        
        return True
    except Exception as e:
        print(f"❌ 訪問失敗：{e}")
        return False

def check_playwright():
    """檢查 Playwright 是否可用"""
    print("\n🔍 測試 3: 檢查 Playwright 瀏覽器自動化工具...")
    
    try:
        import playwright
        print(f"✅ Playwright 已安裝！版本：{playwright.__version__}")
        return True
    except ImportError:
        print("⚠️ Playwright 未安裝")
        print("   安裝指令：pip install playwright && playwright install")
        return False

def test_summary():
    """測試總結"""
    print("\n" + "="*50)
    print("📊 測試總結")
    print("="*50)
    
    results = {
        "網站訪問": False,
        "台灣站訪問": False,
        "自動化工具": False
    }
    
    # 執行測試
    results["網站訪問"] = test_coupang_access()
    results["台灣站訪問"] = test_tw_coupang()
    results["自動化工具"] = check_playwright()
    
    print("\n📋 測試結果：")
    for test, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"   {test}: {status}")
    
    # 可行性評估
    print("\n🎯 可行性評估：")
    if all(results.values()):
        print("✅ 完全可行！可以實作自動登入系統")
    elif results["網站訪問"] and results["台灣站訪問"]:
        print("⚠️ 基本可行，但需要安裝 Playwright")
        print("   只需執行：pip install playwright && playwright install chromium")
    else:
        print("❌ 需要進一步調查")
    
    return results

if __name__ == "__main__":
    print("🧪 Coupang 自動化技術可行性測試")
    print("="*50)
    results = test_summary()
    
    # 輸出 JSON 報告
    with open('coupang_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n📄 詳細報告已儲存：coupang_test_report.json")
