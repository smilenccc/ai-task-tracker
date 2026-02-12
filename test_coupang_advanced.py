#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coupang 深度測試 - 使用真實瀏覽器
測試登入頁面結構和訂單頁面可訪問性
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_coupang_with_browser():
    """使用 Playwright 真實瀏覽器測試"""
    
    print("🚀 啟動瀏覽器測試...")
    print("="*60)
    
    results = {
        "browser_launch": False,
        "tw_coupang_access": False,
        "login_page_found": False,
        "login_form_structure": {},
        "anti_bot_detected": False,
        "recommendations": []
    }
    
    try:
        with sync_playwright() as p:
            # 啟動瀏覽器
            print("\n📦 步驟 1: 啟動 Chromium 瀏覽器...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            results["browser_launch"] = True
            print("   ✅ 瀏覽器啟動成功")
            
            # 訪問台灣 Coupang
            print("\n🌐 步驟 2: 訪問 tw.coupang.com...")
            try:
                page.goto('https://tw.coupang.com', wait_until='networkidle', timeout=15000)
                results["tw_coupang_access"] = True
                print("   ✅ 成功訪問 tw.coupang.com")
                print(f"   頁面標題：{page.title()}")
            except Exception as e:
                print(f"   ❌ 訪問失敗：{e}")
                results["recommendations"].append("tw.coupang.com 可能需要驗證或不支援台灣")
            
            # 尋找登入相關元素
            print("\n🔍 步驟 3: 尋找登入頁面...")
            
            # 嘗試多種方式尋找登入連結
            login_selectors = [
                'a:has-text("登入")',
                'a:has-text("登录")',
                'a:has-text("Login")',
                'button:has-text("登入")',
                '[href*="login"]',
                '[href*="signin"]',
            ]
            
            login_found = False
            for selector in login_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"   ✅ 找到登入元素：{selector} ({len(elements)} 個)")
                        login_found = True
                        
                        # 嘗試點擊第一個登入連結
                        try:
                            elements[0].click(timeout=5000)
                            page.wait_for_load_state('networkidle', timeout=5000)
                            print(f"   ✅ 已進入登入頁面：{page.url}")
                            results["login_page_found"] = True
                            break
                        except:
                            pass
                except:
                    continue
            
            if not login_found:
                print("   ⚠️ 未找到明顯的登入連結")
                results["recommendations"].append("可能需要直接訪問登入頁面 URL")
            
            # 分析登入表單結構
            if results["login_page_found"]:
                print("\n📋 步驟 4: 分析登入表單結構...")
                
                # 尋找表單元素
                form_elements = {
                    "email_input": page.query_selector('input[type="email"], input[name*="email"], input[placeholder*="email"]'),
                    "password_input": page.query_selector('input[type="password"]'),
                    "submit_button": page.query_selector('button[type="submit"], input[type="submit"]'),
                    "captcha": page.query_selector('[class*="captcha"], [id*="captcha"]'),
                }
                
                for element_name, element in form_elements.items():
                    if element:
                        print(f"   ✅ 找到：{element_name}")
                        results["login_form_structure"][element_name] = True
                    else:
                        print(f"   ❌ 未找到：{element_name}")
                        results["login_form_structure"][element_name] = False
                
                # 檢測反機器人機制
                if form_elements["captcha"]:
                    results["anti_bot_detected"] = True
                    print("   ⚠️ 偵測到 CAPTCHA 驗證碼")
                    results["recommendations"].append("需要處理 CAPTCHA 驗證")
                
                # 截圖
                try:
                    page.screenshot(path='coupang_login_page.png')
                    print("   📸 登入頁面截圖已儲存：coupang_login_page.png")
                except:
                    pass
            
            # 關閉瀏覽器
            browser.close()
            print("\n✅ 瀏覽器測試完成")
            
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤：{e}")
        results["error"] = str(e)
    
    return results

def print_summary(results):
    """印出測試總結"""
    print("\n" + "="*60)
    print("📊 測試總結報告")
    print("="*60)
    
    print("\n✅ 測試結果：")
    print(f"   瀏覽器啟動：{'✅ 成功' if results['browser_launch'] else '❌ 失敗'}")
    print(f"   訪問 tw.coupang.com：{'✅ 成功' if results['tw_coupang_access'] else '❌ 失敗'}")
    print(f"   找到登入頁面：{'✅ 是' if results['login_page_found'] else '❌ 否'}")
    print(f"   偵測到反機器人：{'⚠️ 是' if results['anti_bot_detected'] else '✅ 否'}")
    
    if results['login_form_structure']:
        print("\n📋 登入表單結構：")
        for key, value in results['login_form_structure'].items():
            status = '✅' if value else '❌'
            print(f"   {status} {key}")
    
    if results['recommendations']:
        print("\n💡 建議：")
        for rec in results['recommendations']:
            print(f"   • {rec}")
    
    # 可行性評估
    print("\n🎯 自動化可行性評估：")
    if results['browser_launch'] and results['tw_coupang_access'] and results['login_page_found']:
        if results['anti_bot_detected']:
            print("   ⚠️ 技術可行，但需要處理驗證碼")
            print("   建議：")
            print("      1. 使用 Session Cookie（登入一次，保存 Cookie）")
            print("      2. 或請用戶手動完成驗證後再自動化")
        else:
            print("   ✅ 完全可行！可以實作自動登入和訂單抓取")
    elif results['browser_launch'] and results['tw_coupang_access']:
        print("   ⚠️ 部分可行，需要找到正確的登入頁面")
    else:
        print("   ❌ 目前不可行，需要進一步調查")

if __name__ == "__main__":
    print("🧪 Coupang 深度自動化測試")
    print("="*60)
    print("使用真實瀏覽器模擬人類訪問\n")
    
    results = test_coupang_with_browser()
    print_summary(results)
    
    # 儲存報告
    with open('coupang_advanced_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n📄 詳細報告已儲存：coupang_advanced_report.json")
