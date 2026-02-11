# 🚀 防火牆查看系統 - Render 部署指南

## 📋 部署步驟

### 1. 登入 Render

訪問：https://render.com

### 2. 建立新服務

1. 點擊右上角 **"New +"**
2. 選擇 **"Web Service"**

### 3. 連接 GitHub

1. 選擇你的 GitHub 帳號
2. 搜尋並選擇 repository：**ai-task-tracker**
3. 點擊 "Connect"

### 4. 服務設定

填入以下資訊：

```
Name: firewall-viewer
或任何你喜歡的名稱（英文、數字、連字號）

Branch: main

Root Directory: firewall

Runtime: Node

Build Command: npm install

Start Command: npm start

Instance Type: Free
```

### 5. 環境變數（重要！）

點擊 "Advanced" 展開，然後在 "Environment Variables" 區域新增：

**變數 1:**
```
Key: TOTP_SECRET
Value: U3KQHZMQ4UMNVTZYXTPGJ2AGLBRPZR5L
```

**變數 2:**
```
Key: WEBHOOK_URL
Value: http://157.180.126.133:5001
```

**變數 3:**
```
Key: WEBHOOK_SECRET
Value: linda-firewall-webhook-secret-2026
```

**變數 4:**
```
Key: PORT
Value: 10000
```

### 6. 建立服務

點擊 **"Create Web Service"**

Render 會開始：
- 下載程式碼
- 執行 npm install
- 啟動服務

等待 2-3 分鐘...

### 7. 取得網址

部署完成後，在頁面上方會看到你的服務網址，例如：

```
https://firewall-viewer.onrender.com
```

或

```
https://firewall-viewer-xxxx.onrender.com
```

**複製這個網址！**

---

## 🔗 更新 Dashboard 連結

把網址告訴 Linda：

```
Linda，防火牆管理的網址是：https://firewall-viewer.onrender.com
請幫我更新 Dashboard 的連結
```

Linda 會自動更新 `index.html` 中的連結。

---

## ✅ 測試

1. 訪問你的 Render 網址
2. 應該會看到 2FA 登入頁面
3. 輸入 Authy 上的 6 位數驗證碼
4. 登入成功後看到白名單和規則

---

## 🔧 故障排除

### 問題：服務啟動失敗

**檢查：**
1. Render Dashboard → Logs 查看錯誤訊息
2. 確認 `Root Directory` 設定為 `firewall`
3. 確認 `package.json` 存在

### 問題：2FA 驗證失敗

**檢查：**
1. 確認 `TOTP_SECRET` 環境變數設定正確
2. 確認手機時間準確（TOTP 依賴時間同步）
3. 重新掃描 QR code

### 問題：無法載入白名單

**檢查：**
1. 確認 `WEBHOOK_URL` 和 `WEBHOOK_SECRET` 正確
2. 確認 VPS 上的 webhook server 正在運行
3. 檢查防火牆是否允許 5001 port

---

## 🎯 完成後的效果

**在 Dashboard 點擊「防火牆管理」：**

```
1. 跳轉到 Render 網址
   ↓
2. 看到 2FA 登入頁面
   ↓
3. 輸入 Authy 驗證碼
   ↓
4. 登入成功
   ↓
5. 查看白名單和規則
```

---

**準備好了嗎？** 開始部署！ 🚀
