# OpenClaw Tool Calling — 讓 AI 控制手機

## 目標

目前 OpenClaw 只能回覆文字。我們要讓 AI 可以透過 WebSocket 控制 Android 手機的功能：拍照、開啟導航、播放/停止音樂、開啟 App。

## 現有架構

```
Android App ←WebSocket→ chat-server (Python/FastAPI) ←HTTP→ OpenClaw Gateway ←→ Anthropic Claude
```

## 完整流程

```
用戶："幫我拍一張照片"

1. Android 送 {"type":"message","content":"幫我拍照"} 到 chat-server
2. chat-server 帶 tools[] 定義送給 OpenClaw Gateway（/v1/chat/completions）
3. OpenClaw/Claude 回應 tool_calls: [{name:"take_photo"}]
4. chat-server 送 {"type":"tool_call","tool_call_id":"xxx","tool_name":"take_photo"} 給 Android
5. Android 執行 SDK 拍照 → 等 callback
6. Android 送 {"type":"tool_result","tool_call_id":"xxx","content":"拍照成功"} 回 chat-server
7. chat-server 把結果送回 OpenClaw → OpenClaw 產生最終回覆
8. chat-server 送 {"type":"reply","content":"好的，已經幫你拍了一張照片！"} 給 Android
```

## 關鍵問題：OpenClaw Gateway 是否支援 tool calling？

我們的 chat-server 透過 `/v1/chat/completions` API 送請求給 OpenClaw，需要帶 `tools[]` 參數：

```json
{
  "messages": [{"role":"user","content":"幫我拍照"}],
  "tools": [
    {"type":"function","function":{"name":"take_photo","description":"Take a photo","parameters":{"type":"object","properties":{}}}}
  ]
}
```

### 需要 OpenClaw 做到的事

1. **接收 `tools[]` 參數** — 不要擋掉，原封不動轉給 Anthropic Claude API
2. **回傳 `tool_calls`** — Claude 回覆中的 `tool_calls` 要正確傳回給 chat-server

### 測試方式

在 Hetzner 上用 curl 測試（需先確認 OpenClaw Gateway 正在運行）：

```bash
# 先確認 Gateway 有在跑
systemctl status openclaw
ss -tlnp | grep 18789

# 測試帶 tools 的請求
curl -v -X POST http://localhost:18789/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <OPENCLAW_TOKEN>" \
  -d '{"messages":[{"role":"user","content":"幫我拍照"}],"tools":[{"type":"function","function":{"name":"take_photo","description":"Take a photo","parameters":{"type":"object","properties":{}}}}]}'
```

### 期望回應

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "tool_calls": [{
        "id": "call_xxx",
        "type": "function",
        "function": {"name": "take_photo", "arguments": "{}"}
      }]
    },
    "finish_reason": "tool_calls"
  }]
}
```

### 如果 OpenClaw 不支援 tool calling 的替代方案

1. **方案 A：升級 OpenClaw** — 看新版本是否支援 tool passing
2. **方案 B：繞過 OpenClaw，直接打 Anthropic API** — 改 chat-server 的 bridge.py，直接用 `https://api.anthropic.com/v1/messages`，需要 Anthropic API Key

## 已完成的程式碼改動

程式碼已經寫好並推到 GitHub（`smilenccc/android-audioconnect-openclaw`），等確認 OpenClaw 支援 tool calling 後就能用。

### 定義的 5 個 Tools

| Tool 名稱 | 功能 | 參數 |
|-----------|------|------|
| `take_photo` | 用 SDK 拍照 | 無 |
| `open_navigation` | 開啟 Google Maps 導航 | `destination`（目的地） |
| `play_music` | 播放音樂 | 無 |
| `stop_music` | 停止音樂 | 無 |
| `open_app` | 開啟 App | `app_name`（App 名稱或 package name） |

### 修改的檔案

#### Server 端（Python chat-server）— 4 個檔案

| 檔案 | 動作 | 說明 |
|------|------|------|
| `models.py` | 修改 | 加 `tool_result` / `tool_call` 訊息類型 |
| `tools.py` | **新增** | 5 個 Tool 定義 + AI system prompt |
| `bridge.py` | 修改 | 加 `send_message_with_tools()` 和 `continue_with_tool_result()` |
| `server.py` | 修改 | WebSocket 改用 asyncio Queue 架構，支援 tool_call 來回，30 秒超時 |

#### Android 端（Kotlin）— Button 6 的 2 個檔案

| 檔案 | 動作 | 說明 |
|------|------|------|
| `OpenClawClient.kt` | 修改 | 加 `ToolCallHandler` 介面、處理 `tool_call` 訊息、送 `tool_result` |
| `OpenClawChatActivity.kt` | 修改 | 實作 5 個 tool executor（拍照、導航、音樂、開 App） |

## WebSocket 訊息格式

### 新增：Server → Android（tool_call）

```json
{
  "type": "tool_call",
  "tool_call_id": "call_abc123",
  "tool_name": "take_photo",
  "tool_arguments": "{}",
  "timestamp": 1707500000000
}
```

### 新增：Android → Server（tool_result）

```json
{
  "type": "tool_result",
  "tool_call_id": "call_abc123",
  "content": "Photo taken successfully"
}
```

## 部署步驟

1. **確認 OpenClaw Gateway 支援 tool calling**（用上面的 curl 測試）
2. **更新 Hetzner 上的 chat-server** — `git pull` + `systemctl restart openclaw-chat`
3. **Build APK** — `adb install`
4. **測試指令**：
   - "幫我播放音樂" → 觸發 `play_music`
   - "打開 YouTube" → 觸發 `open_app`
   - "導航到台北車站" → 觸發 `open_navigation`
   - "幫我拍照" → 觸發 `take_photo`（需藍牙裝置）
   - "今天天氣如何" → 不觸發任何 tool，正常回覆文字
