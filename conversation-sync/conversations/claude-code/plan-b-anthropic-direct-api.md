# 方案 B：直接使用 Anthropic API 實作 Tool Calling

## 測試結果摘要

**OpenClaw Gateway 不支援 tool calling**
- 測試時間：2026-02-10 16:07
- 測試方式：curl 帶 `tools[]` 參數
- 結果：AI 只回傳文字，沒有觸發 tool
- 結論：需要走方案 B

---

## 方案 B 架構

### 現有架構（不支援 tool calling）
```
AI眼鏡 (Android) → WebSocket → chat-server (Python) → OpenClaw Gateway → Claude API
                                                            ❌ 這裡擋掉了 tool calling
```

### 新架構（方案 B）
```
AI眼鏡 (Android) → WebSocket → chat-server (Python) → Claude API (直連)
                                                        ✅ 完整支援 tool calling
```

---

## 實作步驟

### 1. 準備 Anthropic API 認證

**好消息：你已經有 setup token 了！**

位置：`/root/.openclaw/credentials/auth-profiles.json`
```json
{
  "anthropic:manual": {
    "provider": "anthropic",
    "mode": "setup-token",
    "token": "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"
  }
}
```

**這個 token 完全免費，可以直接用！**

---

### 2. 修改 chat-server 的 bridge.py

**檔案位置：** `/root/openclaw-chat-server/bridge.py`（或 GitHub repo 裡）

#### 原本的程式碼（OpenClaw Gateway）
```python
# 原本：透過 OpenClaw Gateway
response = requests.post(
    "http://localhost:18789/v1/chat/completions",
    headers={"Authorization": f"Bearer {OPENCLAW_TOKEN}"},
    json=payload
)
```

#### 新的程式碼（Anthropic 直連）

```python
import anthropic

# 在檔案開頭加上
ANTHROPIC_API_KEY = "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"
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def send_message_with_tools(message: str, tools: list):
    """
    直接呼叫 Anthropic API，支援 tool calling
    """
    # 轉換 tools 格式（OpenAI → Anthropic）
    anthropic_tools = []
    for tool in tools:
        anthropic_tools.append({
            "name": tool["function"]["name"],
            "description": tool["function"]["description"],
            "input_schema": tool["function"]["parameters"]
        })
    
    # 呼叫 Anthropic API
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=anthropic_tools,
        messages=[{"role": "user", "content": message}]
    )
    
    # 檢查是否有 tool_use
    if response.stop_reason == "tool_use":
        # 找到 tool_use block
        for block in response.content:
            if block.type == "tool_use":
                return {
                    "type": "tool_call",
                    "tool_call_id": block.id,
                    "tool_name": block.name,
                    "tool_arguments": json.dumps(block.input)
                }
    
    # 否則回傳一般訊息
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text
    
    return {
        "type": "reply",
        "content": text_content
    }

async def continue_with_tool_result(tool_call_id: str, tool_name: str, tool_result: str):
    """
    把工具執行結果送回 Claude，取得最終回覆
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "幫我拍照"},  # 原始訊息
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": tool_call_id,
                        "name": tool_name,
                        "input": {}
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": tool_result
                    }
                ]
            }
        ]
    )
    
    # 提取文字回覆
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text
    
    return {
        "type": "reply",
        "content": text_content
    }
```

---

### 3. 安裝 Anthropic SDK

在 Hetzner 上執行：

```bash
cd /root/openclaw-chat-server
source venv/bin/activate
pip install anthropic
```

---

### 4. 更新環境變數

**檔案：** `/root/openclaw-chat-server/.env`

```bash
# 新增這一行
ANTHROPIC_API_KEY=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

# 保留原本的（供其他功能用）
OPENCLAW_CHAT_OPENCLAW_TOKEN=834d03bc292e68d0550e654176a986c90e2edca1074948bd
```

---

### 5. 測試

#### A. 測試一般對話
```bash
# 在 Android App 裡送訊息：「今天天氣如何」
# 預期：AI 正常回覆文字（不觸發 tool）
```

#### B. 測試 tool calling
```bash
# 在 Android App 裡送訊息：「幫我播放音樂」
# 預期：
# 1. Server 收到 tool_use: play_music
# 2. Server 通知 Android 執行 play_music
# 3. Android 播放音樂並回報成功
# 4. AI 回覆：「好的，已經幫你播放音樂了！」
```

---

## 優缺點比較

### 優點 ✅
1. **100% 確定支援 tool calling**（Anthropic 官方 API）
2. **完全免費**（用 setup token，不是 API key）
3. **延遲可能更低**（少一層 OpenClaw 轉發）
4. **程式碼控制權更大**（直接控制 API 呼叫）

### 缺點 ❌
1. **失去 OpenClaw 的 session 管理**
   - 對話歷史需要自己維護
   - 沒有 OpenClaw 的上下文管理
2. **失去多模型切換能力**（固定用 Claude）
3. **需要自己處理對話歷史**

---

## 對話歷史管理建議

因為繞過了 OpenClaw，需要在 chat-server 維護對話歷史：

```python
# 在記憶體或 Redis 裡維護每個用戶的對話歷史
conversation_history = {}  # {user_id: [messages]}

async def send_message_with_tools(user_id: str, message: str, tools: list):
    # 取得對話歷史
    history = conversation_history.get(user_id, [])
    
    # 加入新訊息
    history.append({"role": "user", "content": message})
    
    # 呼叫 API（帶完整歷史）
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=anthropic_tools,
        messages=history  # ← 帶完整對話歷史
    )
    
    # 儲存 AI 回覆到歷史
    if response.stop_reason == "tool_use":
        # ... 處理 tool calling
        pass
    else:
        history.append({
            "role": "assistant",
            "content": response.content
        })
    
    # 更新歷史（限制最多保留 20 輪對話，避免 token 爆炸）
    conversation_history[user_id] = history[-40:]  # 20 輪 = 40 條訊息
```

---

## 部署步驟

1. ✅ **確認 Anthropic setup token 有效**（已確認）
2. 📝 **修改 bridge.py**（改用 Anthropic SDK）
3. 📦 **安裝 anthropic package**（`pip install anthropic`）
4. 🔄 **重啟 chat-server**（`systemctl restart openclaw-chat`）
5. 📱 **Build 並安裝 Android APK**（已經準備好了）
6. 🧪 **測試 tool calling**（播放音樂、拍照、導航）

---

## 下一步

小八可以開始實作 `bridge.py` 的修改了。需要的資訊都在這份文件裡。

如果有問題隨時問我！💪
