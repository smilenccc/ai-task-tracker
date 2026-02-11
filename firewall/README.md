# 🛡️ Linda 防火牆管理系統 (Webhook 架構)

## 📐 系統架構

```
┌─────────────────┐
│  Render 前端    │  ← 用戶訪問
│  (Node.js)      │
│  - 2FA 認證     │
│  - 網頁界面     │
└────────┬────────┘
         │ HTTPS + API Key
         ↓
┌─────────────────┐
│  VPS Webhook    │  ← 只監聽 localhost
│  (Python Flask) │
│  - 執行 UFW     │
│  - 管理防火牆   │
└─────────────────┘
```

---

## 🚀 部署步驟

### 1️⃣ VPS 端（Webhook Server）

**啟動 Webhook Server：**
```bash
cd /root/.openclaw/workspace/firewall
python3 webhook_server.py &
```

**設定開機自動啟動（可選）：**
```bash
# 建立 systemd service
sudo nano /etc/systemd/system/firewall-webhook.service
```

內容：
```ini
[Unit]
Description=Linda Firewall Webhook Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/firewall
ExecStart=/usr/bin/python3 webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

啟動：
```bash
sudo systemctl daemon-reload
sudo systemctl enable firewall-webhook
sudo systemctl start firewall-webhook
```

**設定 SSH Tunnel（讓 Render 可以連線）：**

方法 A - 使用 Tailscale（推薦）：
1. VPS 和 Render 都安裝 Tailscale
2. Webhook URL 使用 Tailscale IP：`http://100.x.x.x:5001`

方法 B - 反向 SSH Tunnel：
```bash
# 在 VPS 上執行（將 5001 轉發到公開 port）
ssh -R 0.0.0.0:5001:localhost:5001 user@render-server
```

方法 C - ngrok（測試用）：
```bash
ngrok http 5001
# 取得 HTTPS URL，例如：https://abc123.ngrok.io
```

---

### 2️⃣ Render 端（前端）

**部署到 Render：**

1. **推送到 GitHub：**
```bash
cd /root/.openclaw/workspace/task-tracker
git add firewall/
git commit -m "新增防火牆管理前端"
git push origin main
```

2. **在 Render 建立新服務：**
   - 登入 https://render.com
   - 選擇 "New +" → "Web Service"
   - 連接你的 GitHub repo：`ai-task-tracker`
   - 設定：
     - **Name:** `linda-firewall`
     - **Root Directory:** `firewall`
     - **Build Command:** `npm install`
     - **Start Command:** `npm start`
     - **Plan:** Free

3. **設定環境變數：**
   在 Render Dashboard → Environment 新增：
   ```
   TOTP_SECRET = U3KQHZMQ4UMNVTZYXTPGJ2AGLBRPZR5L
   WEBHOOK_URL = http://你的VPS_Tailscale_IP:5001
   WEBHOOK_SECRET = linda-firewall-webhook-secret-2026
   ```

4. **部署：**
   - Render 會自動開始部署
   - 完成後會得到一個網址，例如：
     `https://linda-firewall.onrender.com`

---

## 🔐 訪問方式

### 網址
```
https://linda-firewall.onrender.com
```

### 登入步驟
1. 打開網址
2. 輸入 Authy 上的 6 位數驗證碼
3. 登入成功後可以管理白名單

---

## 🛠️ 本地測試

### 測試 Webhook Server
```bash
# 啟動 webhook server
cd /root/.openclaw/workspace/firewall
python3 webhook_server.py

# 測試（另一個終端機）
curl -H "X-API-Key: linda-firewall-webhook-secret-2026" \
     http://localhost:5001/webhook/health
```

### 測試前端
```bash
# 安裝依賴
cd /root/.openclaw/workspace/task-tracker/firewall
npm install

# 設定環境變數
export WEBHOOK_URL=http://localhost:5001
export WEBHOOK_SECRET=linda-firewall-webhook-secret-2026

# 啟動
npm start

# 訪問 http://localhost:10002
```

---

## 🔑 安全說明

### API Key 認證
- Render 前端 → VPS Webhook：使用 `WEBHOOK_SECRET`
- 前端 → Render API：使用會話 token（2FA 後取得）

### Webhook 安全
- 只監聽 `localhost:5001`
- 需要正確的 API Key
- 建議透過 Tailscale VPN 訪問

### 2FA 認證
- 使用 TOTP（Time-based One-Time Password）
- 與 Google Authenticator、Authy 相容
- Secret 儲存在 Render 環境變數中

---

## 📊 檔案結構

```
task-tracker/firewall/
├── server.mjs          # Node.js 後端（處理 2FA + 轉發）
├── index.html          # 前端網頁
├── package.json        # Node.js 依賴
├── render.yaml         # Render 部署設定
└── README.md           # 本文件
```

---

## 🐛 故障排除

### 問題：無法連線到 Webhook
**解決方案：**
1. 確認 VPS 上的 webhook server 正在運行
2. 確認 Render 環境變數 `WEBHOOK_URL` 設定正確
3. 確認防火牆規則允許連線（Tailscale 或 SSH tunnel）

### 問題：2FA 驗證失敗
**解決方案：**
1. 確認伺服器時間正確：`date`
2. 確認 `TOTP_SECRET` 環境變數正確
3. 重新掃描 QR code

### 問題：Render 部署失敗
**解決方案：**
1. 檢查 build logs
2. 確認 `package.json` 正確
3. 確認 Node.js 版本 >= 18

---

## 📝 維護

### 更新前端
```bash
cd /root/.openclaw/workspace/task-tracker
# 修改 firewall/ 下的檔案
git add firewall/
git commit -m "更新防火牆前端"
git push origin main
# Render 會自動重新部署
```

### 重啟 Webhook Server
```bash
# systemd
sudo systemctl restart firewall-webhook

# 手動
pkill -f webhook_server.py
cd /root/.openclaw/workspace/firewall
python3 webhook_server.py &
```

### 查看日誌
```bash
# Webhook 日誌
tail -f /root/.openclaw/workspace/firewall/logs/firewall.log

# Render 日誌
在 Render Dashboard 查看
```

---

**建立日期：** 2026-02-11  
**維護者：** Linda (AI Assistant)  
**架構版本：** Webhook 1.0
