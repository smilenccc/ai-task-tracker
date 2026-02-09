# 2026-02-09 下午 — OpenClaw Android 整合工作

## 摘要

小八在 Android AudioConnect SDK (`sample-smartwear`) 的 Button 6 (OpenClaw AI) 做了以下工作：

## 問題診斷

- Button 6 原本直接用 HTTP 連 `157.180.126.133:18789`，但 OpenClaw Gateway 只監聽 `127.0.0.1:18789`（localhost），外部連不到
- Port 掃描確認只有 SSH (22) 對外開放
- Telegram bot (小Linda) 能用是因為 OpenClaw 主動輪詢 Telegram API，不需要 inbound port

## 已完成

### 1. Hetzner 部署 chat-server (Python FastAPI WebSocket Bridge)
- 上傳 `sample/chat-server` 到 Hetzner `/root/openclaw-chat-server`
- 安裝 Python venv + 所有依賴 (FastAPI, uvicorn, websockets, httpx)
- 建立 `openclaw-chat.service` systemd 服務，開機自動啟動
- **Port 8200** 對外可連，health check 正常
- 架構: `Android App → ws://157.180.126.133:8200/chat → chat-server → localhost:18789 → OpenClaw Gateway`

### 2. 改寫 Button 6 為 WebSocket 模式
- `OpenClawClient.kt` — 從 HttpURLConnection 改為 OkHttp WebSocket
  - 自動轉換 http:// → ws:// URL
  - `chat()` 用 CountDownLatch 保持同步介面
  - 支援連線狀態監聽
- `OpenClawChatActivity.kt` — 預設 URL 改為 `:8200`，onCreate 自動連 WebSocket
- `AndroidManifest.xml` (sample-smartwear) — 加 `usesCleartextTraffic="true"`
- `network_security_config.xml` (sample) — 加 `157.180.126.133` 到明文白名單

## 待完成

- **重新 build APK 測試連線** — 最後一次截圖仍顯示 "Connection FAILED"
  - 已修正 `network_security_config.xml` 白名單問題，需要重新編譯測試
- Bearer Token 欄位留空即可（server 未啟用客戶端驗證）

## 修改的檔案

1. `src/sample-smartwear/src/main/java/.../openclaw/OpenClawClient.kt` — 全面改寫為 WebSocket
2. `src/sample-smartwear/src/main/java/.../openclaw/OpenClawChatActivity.kt` — 適配 WebSocket client
3. `src/sample-smartwear/src/main/AndroidManifest.xml` — 加 usesCleartextTraffic
4. `src/sample/src/main/res/xml/network_security_config.xml` — 加 Hetzner IP 白名單

## Hetzner 服務狀態

- `openclaw-chat.service` — active (running), port 8200
- OpenClaw Gateway — active, port 18789 (localhost only)
- `taskdash.service` — active (OpenClaw tasks dashboard)
