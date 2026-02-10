# 🚀 Render 部署指南

## 📋 快速部署步驟

### 1️⃣ 登入 Render
訪問：https://dashboard.render.com/

### 2️⃣ 建立新服務
1. 點擊右上角 **「New +」**
2. 選擇 **「Web Service」**

### 3️⃣ 連接 GitHub
1. 選擇倉庫：**`smilenccc/ai-task-tracker`**
2. （如果是第一次，需要授權 Render 訪問你的 GitHub）

### 4️⃣ 設定服務

填入以下資訊：

| 欄位 | 值 |
|------|-----|
| **Name** | `credit-card-dashboard` |
| **Region** | Singapore (或你偏好的區域) |
| **Branch** | `main` |
| **Root Directory** | （留空） |
| **Runtime** | `Node` |
| **Build Command** | `npm install` |
| **Start Command** | `node credit-card/server.mjs` |
| **Instance Type** | `Free` |

### 5️⃣ 環境變數（可選）

不需要設定，系統會自動使用 Render 提供的 `PORT` 環境變數。

### 6️⃣ 建立服務

點擊底部的 **「Create Web Service」** 按鈕

---

## ⏳ 部署進度

部署通常需要 **2-5 分鐘**：

1. ⚙️ Building...（安裝依賴）
2. 🚀 Deploying...（啟動服務）
3. ✅ Live（上線成功）

---

## 🌐 取得網址

部署成功後，網址格式：
```
https://credit-card-dashboard.onrender.com
```

或者在 Render Dashboard 複製你的服務網址。

---

## 🔄 自動部署

設定完成後，**每次推送到 GitHub** Render 會自動重新部署！

---

## 🐛 故障排除

### 問題：Build 失敗

**檢查項目：**
- Build Command 是否正確：`npm install`
- Start Command 是否正確：`node credit-card/server.mjs`

### 問題：服務啟動失敗

**查看日誌：**
1. 進入服務 Dashboard
2. 點擊「Logs」標籤
3. 查看錯誤訊息

### 問題：無法訪問網站

**確認：**
- 服務狀態是否為「Live」（綠色）
- 網址是否正確
- 可能需要等待 DNS 生效（1-2 分鐘）

---

## 📊 監控

在 Render Dashboard 可以查看：
- 📈 CPU / Memory 使用率
- 📝 應用程式日誌
- 🔄 部署歷史記錄

---

## 💡 提示

1. **Free Plan 限制：**
   - 15 分鐘無活動後會自動休眠
   - 訪問時會有 30 秒-1 分鐘的冷啟動時間
   - 每月 750 小時免費（足夠個人使用）

2. **保持活躍：**
   - 可以設定定時 ping 服務（例如每 10 分鐘）
   - 或升級到付費方案（$7/月）

---

**🎉 完成！現在你有一個線上的信用卡消費統計網站了！**
