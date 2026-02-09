# 2026-02-09 Coupang 消費分析網站建置

## 對話摘要

小八幫小八（用戶）建立了完整的 Coupang 酷澎消費分析系統。

## 完成的工作

### 1. 爬蟲嘗試與最終方案
- 最初嘗試用 Playwright + stealth 插件自動爬取，但 Coupang 的 `mc.tw.coupang.com` 子域名有嚴格的 Akamai CDN 保護
- `www.tw.coupang.com` 首頁可以正常存取，但訂單頁（在 mc 子域名）被擋
- 最終採用 **Tampermonkey + 本地 Server** 方案，完全自動化

### 2. 建立的檔案
- `coupang-scraper/scraper.mjs` — Playwright stealth 爬蟲（備用）
- `coupang-scraper/config.mjs` — 分類規則、URL 設定
- `coupang-scraper/console-script.js` — Chrome Console 手動提取腳本
- `coupang-scraper/extract-orders.mjs` — JSON 合併工具
- `coupang-scraper/coupang-tampermonkey.user.js` — **Tampermonkey 自動提取腳本**
- `coupang/index.html` — 消費分析儀表板（深色主題、Chart.js 圖表）
- `coupang/server.mjs` — **Express 本地 Server**（接收訂單 + 提供網頁）
- `coupang/start-server.vbs` — 開機自動啟動 server
- `.env` — Coupang 登入憑證
- `.gitignore` — 排除敏感檔案

### 3. 自動化流程（已設定完成）
1. Windows 開機 → server 自動啟動（背景執行，port 5566）
2. 用戶在 Chrome 打開 Coupang 訂單頁 → Tampermonkey 自動提取訂單
3. 資料自動傳送到 localhost:5566 → 合併去重 → 儲存到 purchases.json
4. 打開 http://localhost:5566/index.html 看儀表板

### 4. 目前資料
- 8 筆訂單，總消費 NT$3,574
- 分類：食品/飲料、日用品/清潔、母嬰/寵物
- 日期範圍：2026-01-20 ~ 2026-02-08

## 技術發現
- Coupang 台灣的訂單頁 URL：`https://mc.tw.coupang.com/ssr/desktop/order/list`
- 頁面使用 Next.js + styled-components（class 名稱是隨機 hash）
- 訂單卡片選擇器：`div.sc-fimazj-0`
- 商品詳情選擇器：`div.sc-9cwg9-5`
- 日期格式：`2026. 2. 8 訂購`

## 待辦
- 翻頁爬取（目前只爬第一頁）— Tampermonkey 腳本可以在每頁自動觸發
- 如果頁面結構改變，需更新 Tampermonkey 腳本中的選擇器
