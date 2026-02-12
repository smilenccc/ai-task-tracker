#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coupang 自動登入並抓取訂單
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
import time
from datetime import datetime
import re

def load_credentials():
    """讀取 Coupang 憑證"""
    creds = {}
    with open('.coupang_credentials', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                creds[key] = value
    return creds

def login_coupang(page, email, password):
    """登入 Coupang"""
    print("\n🔐 開始登入...")
    
    try:
        # 前往登入頁面
        print("   📱 前往 tw.coupang.com...")
        page.goto('https://tw.coupang.com', wait_until='networkidle', timeout=30000)
        
        # 等待頁面載入
        time.sleep(3)
        
        # 尋找登入按鈕/連結
        print("   🔍 尋找登入按鈕...")
        
        # 可能的登入按鈕選擇器
        login_selectors = [
            'text=登入',
            'text=登录',
            'text=Login',
            'a[href*="login"]',
            'button:has-text("登入")',
        ]
        
        login_clicked = False
        for selector in login_selectors:
            try:
                if page.locator(selector).count() > 0:
                    print(f"   ✅ 找到登入按鈕：{selector}")
                    page.locator(selector).first.click()
                    login_clicked = True
                    page.wait_for_load_state('networkidle', timeout=10000)
                    break
            except:
                continue
        
        if not login_clicked:
            print("   ⚠️ 未找到登入按鈕，可能已經在登入頁面")
        
        # 等待登入表單
        time.sleep(2)
        
        # 輸入帳號
        print("   📧 輸入帳號...")
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email"]',
            'input[id*="email"]',
        ]
        
        email_filled = False
        for selector in email_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.fill(selector, email)
                    email_filled = True
                    print(f"   ✅ 已輸入帳號")
                    break
            except:
                continue
        
        if not email_filled:
            print("   ❌ 找不到帳號輸入框")
            return False
        
        time.sleep(1)
        
        # 輸入密碼
        print("   🔑 輸入密碼...")
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
        ]
        
        password_filled = False
        for selector in password_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.fill(selector, password)
                    password_filled = True
                    print(f"   ✅ 已輸入密碼")
                    break
            except:
                continue
        
        if not password_filled:
            print("   ❌ 找不到密碼輸入框")
            return False
        
        time.sleep(1)
        
        # 點擊登入按鈕
        print("   🚀 點擊登入按鈕...")
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("登入")',
            'button:has-text("登录")',
            'button:has-text("Login")',
        ]
        
        submit_clicked = False
        for selector in submit_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click()
                    submit_clicked = True
                    print(f"   ✅ 已點擊登入")
                    break
            except:
                continue
        
        if not submit_clicked:
            print("   ❌ 找不到登入按鈕")
            return False
        
        # 等待登入完成
        print("   ⏳ 等待登入完成...")
        time.sleep(5)
        
        # 檢查是否登入成功
        # 通常登入成功後會有「我的帳戶」或用戶名顯示
        success_indicators = [
            'text=我的帳戶',
            'text=我的訂單',
            'text=會員中心',
            '[href*="mypage"]',
        ]
        
        login_success = False
        for indicator in success_indicators:
            try:
                if page.locator(indicator).count() > 0:
                    login_success = True
                    print(f"   ✅ 登入成功！偵測到：{indicator}")
                    break
            except:
                continue
        
        if login_success:
            # 截圖
            try:
                page.screenshot(path='coupang_login_success.png')
                print("   📸 登入成功截圖已儲存")
            except:
                pass
            return True
        else:
            # 檢查是否有錯誤訊息
            page.screenshot(path='coupang_login_failed.png')
            print("   ⚠️ 無法確認登入狀態，截圖已儲存")
            print(f"   當前 URL: {page.url}")
            return False
    
    except Exception as e:
        print(f"   ❌ 登入過程發生錯誤：{e}")
        try:
            page.screenshot(path='coupang_login_error.png')
        except:
            pass
        return False

def scrape_orders(page):
    """抓取訂單資訊"""
    print("\n📦 開始抓取訂單...")
    
    try:
        # 前往訂單頁面
        print("   🔗 前往我的訂單頁面...")
        
        # 可能的訂單頁面路徑
        order_urls = [
            'https://tw.coupang.com/mypage/orders',
            'https://tw.coupang.com/my/orders',
            'https://tw.coupang.com/orders',
        ]
        
        orders_page_loaded = False
        for url in order_urls:
            try:
                page.goto(url, wait_until='networkidle', timeout=15000)
                time.sleep(3)
                
                # 檢查是否成功載入訂單頁面
                if '訂單' in page.title() or 'order' in page.url.lower():
                    orders_page_loaded = True
                    print(f"   ✅ 成功載入訂單頁面")
                    break
            except:
                continue
        
        if not orders_page_loaded:
            print("   ⚠️ 嘗試從選單點擊進入訂單頁面...")
            # 嘗試點擊「我的訂單」連結
            try:
                page.locator('text=我的訂單').first.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(3)
            except:
                print("   ❌ 無法進入訂單頁面")
                return []
        
        # 截圖
        try:
            page.screenshot(path='coupang_orders_page.png', full_page=True)
            print("   📸 訂單頁面截圖已儲存")
        except:
            pass
        
        # 提取訂單資訊
        print("   📋 解析訂單資訊...")
        
        orders = []
        
        # 取得頁面內容
        content = page.content()
        
        # 簡單解析（實際需要根據真實 HTML 結構調整）
        # 這裡先儲存 HTML 供後續分析
        with open('coupang_orders_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("   💾 訂單頁面 HTML 已儲存到 coupang_orders_page.html")
        
        return orders
    
    except Exception as e:
        print(f"   ❌ 抓取訂單時發生錯誤：{e}")
        return []

def main():
    """主程式"""
    print("🤖 Coupang 自動登入系統")
    print("="*60)
    
    # 讀取憑證
    print("\n📋 讀取憑證...")
    creds = load_credentials()
    email = creds['EMAIL']
    password = creds['PASSWORD']
    print(f"   ✅ 帳號：{email}")
    print(f"   ✅ 密碼：{'*' * len(password)}")
    
    # 啟動瀏覽器
    print("\n🚀 啟動瀏覽器...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-TW'
        )
        
        page = context.new_page()
        
        # 登入
        login_success = login_coupang(page, email, password)
        
        if login_success:
            # 抓取訂單
            orders = scrape_orders(page)
            
            print(f"\n📊 找到 {len(orders)} 筆訂單")
        else:
            print("\n❌ 登入失敗")
        
        # 關閉瀏覽器
        browser.close()
    
    print("\n✅ 測試完成")
    print("\n請查看以下檔案分析結果：")
    print("   • coupang_login_success.png / coupang_login_failed.png")
    print("   • coupang_orders_page.png")
    print("   • coupang_orders_page.html")

if __name__ == "__main__":
    main()
