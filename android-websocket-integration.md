# Android WebSocket 整合測試資料

## ✅ 測試成功的配置

### 伺服器資訊
- **IP:** 157.180.126.133
- **Port:** 8200
- **WebSocket 端點:** `ws://157.180.126.133:8200/chat`
- **服務狀態:** ✅ 運行中
- **伺服器:** Hetzner (openlaw)

---

## 📡 連線測試成功記錄

### 測試時間
2026-02-09 21:06 (台北時間)

### 測試結果
```
🧪 OpenClaw WebSocket 完整流程測試
==================================================
📡 連接到: ws://157.180.126.133:8200/chat
✅ WebSocket 連線成功！

📤 發送測試訊息:
   2+2等於多少？只回答數字

⏳ 等待 OpenClaw 回應...

📥 訊息 #1 [類型: connected]
   內容: Connected to OpenClaw Chat (client: b8db0bb7)

📥 訊息 #2 [類型: reply]
   內容: 4

==================================================
🎉 測試成功！收到 OpenClaw 回覆！
==================================================
```

**往返時間:** < 2秒

---

## 📋 訊息格式規範

### 1️⃣ 客戶端發送格式（Android → Server）

```json
{
  "type": "message",
  "content": "你要問的問題或訊息"
}
```

**重要：**
- 必須使用 `type` 和 `content` 欄位
- ❌ 不要用 `message` 欄位（這是錯誤的）
- ✅ 正確：`{"type": "message", "content": "..."}`

### 2️⃣ 伺服器回覆格式（Server → Android）

#### 連線成功訊息（第一個）
```json
{
  "type": "connected",
  "content": "Connected to OpenClaw Chat (client: xxxxxxxx)",
  "timestamp": 1770642376123,
  "error": null
}
```

#### AI 回覆訊息
```json
{
  "type": "reply",
  "content": "AI的回覆內容",
  "timestamp": 1770642377456,
  "error": null
}
```

#### 錯誤訊息
```json
{
  "type": "error",
  "content": "",
  "timestamp": 1770642378789,
  "error": "錯誤描述"
}
```

---

## 🔧 Android 實作要點

### WebSocket 連線參數
```
URL: ws://157.180.126.133:8200/chat
Protocol: WebSocket (ws://)
Headers: 無需特殊 headers
Auth: 無需認證（已在伺服器端處理）
```

### 連線流程
1. **建立 WebSocket 連線** → `ws://157.180.126.133:8200/chat`
2. **等待 connected 訊息** → 確認連線成功
3. **發送訊息** → `{"type": "message", "content": "..."}`
4. **接收回覆** → 監聽 `type: "reply"` 的訊息
5. **解析 content** → 這就是 AI 的回答

### 建議實作邏輯

```kotlin
// 連線成功
onOpen {
    isConnected = true
    // 等待 server 發送 connected 訊息
}

// 收到訊息
onMessage { json ->
    val type = json["type"]
    val content = json["content"]
    
    when (type) {
        "connected" -> {
            // 連線確認，可以開始發送訊息
            showStatus("已連接到小Linda")
        }
        "reply" -> {
            // AI 回覆
            displayResponse(content)
        }
        "error" -> {
            // 錯誤處理
            showError(json["error"])
        }
    }
}

// 發送訊息
fun sendMessage(userInput: String) {
    val message = JSONObject().apply {
        put("type", "message")
        put("content", userInput)
    }
    websocket.send(message.toString())
}
```

---

## 🧪 Python 測試腳本（可用於驗證）

```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://157.180.126.133:8200/chat"
    
    async with websockets.connect(uri) as ws:
        print("✅ 連線成功")
        
        # 發送訊息
        msg = {"type": "message", "content": "你好"}
        await ws.send(json.dumps(msg))
        
        # 接收回覆
        count = 0
        while count < 5:
            response = await asyncio.wait_for(ws.recv(), timeout=20.0)
            data = json.loads(response)
            
            print(f"收到: [{data['type']}] {data.get('content', '')}")
            
            if data['type'] == 'reply':
                break
            count += 1

asyncio.run(test())
```

---

## ⚙️ 伺服器配置（已完成，供參考）

### OpenClaw Gateway 配置
- Port: 18789
- OpenAI Chat Completions 端點: **已啟用**
- Auth Token: `834d03bc292e68d0550e654176a986c90e2edca1074948bd`

### chat-server 配置
- Port: 8200
- Gateway URL: `http://localhost:18789`
- Token: 已配置（與 Gateway 一致）
- 服務: `openclaw-chat.service` (systemd)

---

## 🐛 常見問題排查

### 問題 1: 連線失敗
- 確認使用 `ws://` 而非 `http://`
- 確認 IP 和 Port 正確
- 檢查網路連線

### 問題 2: 收到 error 訊息
- 檢查訊息格式是否正確
- 必須使用 `type` 和 `content` 欄位

### 問題 3: 沒有收到回覆
- 確認已收到 `connected` 訊息後才發送
- 等待時間至少 20 秒（AI 處理時間）
- 檢查是否正確解析 JSON

### 問題 4: 401 Unauthorized
- 伺服器端問題，已解決
- 如果再次出現，通知我檢查 token 配置

---

## 📊 測試檢查清單

- [ ] WebSocket 能成功連線
- [ ] 收到 `connected` 訊息
- [ ] 能發送訊息（格式正確）
- [ ] 能接收 `reply` 訊息
- [ ] 能正確解析 JSON
- [ ] 能顯示 AI 回覆內容
- [ ] 錯誤處理正常

---

## 🔗 相關檔案位置（伺服器端）

- chat-server: `/root/openclaw-chat-server/`
- 服務設定: `/etc/systemd/system/openclaw-chat.service`
- 配置檔: `/root/openclaw-chat-server/.env`
- OpenClaw 配置: `/root/.openclaw/openclaw.json`

---

**整理日期:** 2026-02-09  
**測試者:** 小Linda  
**狀態:** ✅ 測試成功，可供 Android 整合使用
