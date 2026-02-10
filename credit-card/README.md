# 💳 信用卡消費統計系統

## 📊 功能特色

- ✅ 自動分類消費項目
- ✅ 圓餅圖顯示類別分布
- ✅ 長條圖顯示每日消費趨勢
- ✅ 消費明細列表（依金額排序）
- ✅ 響應式設計（支援手機、平板、電腦）

---

## 🚀 本地運行

```bash
cd credit-card
node server.mjs
```

訪問：http://localhost:5567

---

## 🌐 部署到 Render

### 方法 1：使用 Render Dashboard

1. 登入 [Render.com](https://render.com)
2. 點擊「New +」→「Web Service」
3. 連接 GitHub 倉庫：`smilenccc/ai-task-tracker`
4. 設定：
   - **Name:** `credit-card-dashboard`
   - **Build Command:** `npm install`
   - **Start Command:** `node credit-card/server.mjs`
   - **Plan:** Free
5. 點擊「Create Web Service」

### 方法 2：使用 render.yaml

在倉庫根目錄建立 `render.yaml`（或使用 `credit-card-render.yaml`）：

```yaml
services:
  - type: web
    name: credit-card-dashboard
    runtime: node
    plan: free
    buildCommand: npm install
    startCommand: node credit-card/server.mjs
```

推送到 GitHub 後，Render 會自動偵測並部署。

---

## 📂 檔案結構

```
credit-card/
├── index.html          # 前端網頁
├── server.mjs          # Express 伺服器
├── transactions.json   # 消費資料
└── README.md           # 說明文件
```

---

## 🔄 更新資料

更新 `transactions.json` 後：

1. 本地測試：重新啟動 server
2. Render 部署：推送到 GitHub，自動重新部署

---

## 📊 消費類別

系統自動分類：
- 🍴 **餐飲** - 肉圓、豆花、餐廳
- 🚗 **交通** - eTag、運通、特斯拉
- 🛒 **購物** - 康是美、Coupang
- 🎮 **娛樂** - YouTube、海洋館、Apple
- 📱 **訂閱** - 中華電信、會員服務
- 📦 **其他** - 其他消費

---

## 🤖 資料來源

- 玉山銀行信用卡電子帳單（PDF）
- 由小Linda自動提取並處理

---

## 📅 建立時間

2026-02-10

**狀態：** ✅ 已完成
