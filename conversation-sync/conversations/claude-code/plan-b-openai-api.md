# 方案 B：使用 OpenAI API 實作 Tool Calling

## 決策

**用戶選擇：OpenAI API（不用 Anthropic）**
- 日期：2026-02-10
- 原因：OpenClaw Gateway 不支援 client-side tool calling

---

## 架構

### 新架構（方案 B - OpenAI）
```
AI眼鏡 (Android) → WebSocket → chat-server (Python) → OpenAI API (直連)
                                                        ✅ Function Calling
```

**OpenClaw Gateway 保持不變** - 只有 chat-server 改用 OpenAI API

---

## OpenAI API 設定

### 1. 申請 API Key

**網址：** https://platform.openai.com/api-keys

步驟：
1. 登入 OpenAI 帳號
2. 點選 **API Keys**
3. 點選 **Create new secret key**
4. 複製 API Key（格式：`sk-proj-...` 或 `sk-...`）

### 2. 流量控管

**網址：** https://platform.openai.com/settings/organization/limits

可以設定：
- **Hard limit**（硬性上限）- 達到後 API 停止
- **Soft limit**（軟性上限）- 達到後發通知但不停止
- 建議先設定 **$10/月**

### 3. 查看使用量

**網址：** https://platform.openai.com/usage

可以看到：
- 每日/每月使用量
- 按 model 分類的成本
- Token 使用統計

---

## 實作步驟

### Step 1: 安裝 OpenAI SDK

在 Hetzner 上執行：

```bash
cd /root/openclaw-chat-server
source venv/bin/activate
pip install openai
```

### Step 2: 修改 bridge.py

**檔案位置：** `/root/openclaw-chat-server/bridge.py`（或 GitHub repo）

#### 在檔案開頭加上

```python
from openai import OpenAI
import json

# 讀取 OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
```

#### 新增：send_message_with_tools

```python
async def send_message_with_tools(message: str, tools: list, conversation_history: list = None):
    """
    使用 OpenAI API 處理帶 tools 的訊息
    
    Args:
        message: 用戶訊息
        tools: OpenAI function tools 列表
        conversation_history: 對話歷史（格式：[{"role": "user", "content": "..."}]）
    
    Returns:
        dict: {"type": "tool_call", ...} 或 {"type": "reply", ...}
    """
    # 準備 messages（包含歷史）
    messages = conversation_history or []
    messages.append({"role": "user", "content": message})
    
    # 呼叫 OpenAI API
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",  # 或 gpt-4o, gpt-4o-mini
        messages=messages,
        tools=tools,
        tool_choice="auto"  # 讓 AI 自己判斷是否要呼叫工具
    )
    
    choice = response.choices[0]
    message_obj = choice.message
    
    # 檢查是否有 tool_calls
    if message_obj.tool_calls:
        tool_call = message_obj.tool_calls[0]
        return {
            "type": "tool_call",
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.function.name,
            "tool_arguments": tool_call.function.arguments,  # JSON string
            "timestamp": int(time.time() * 1000)
        }
    
    # 否則回傳一般訊息
    return {
        "type": "reply",
        "content": message_obj.content,
        "timestamp": int(time.time() * 1000)
    }
```

#### 新增：continue_with_tool_result

```python
async def continue_with_tool_result(
    conversation_history: list,
    tool_call_id: str,
    tool_name: str,
    tool_arguments: str,
    tool_result: str
):
    """
    把工具執行結果送回 OpenAI，取得最終回覆
    
    Args:
        conversation_history: 原始對話歷史
        tool_call_id: OpenAI 回傳的 tool call ID
        tool_name: 工具名稱
        tool_arguments: 工具參數（JSON string）
        tool_result: 工具執行結果
    
    Returns:
        dict: {"type": "reply", "content": "..."}
    """
    # 加入 assistant 的 tool_call
    conversation_history.append({
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": tool_call_id,
            "type": "function",
            "function": {
                "name": tool_name,
                "arguments": tool_arguments
            }
        }]
    })
    
    # 加入 tool 執行結果
    conversation_history.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": tool_result
    })
    
    # 呼叫 API 取得最終回覆
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=conversation_history
    )
    
    final_message = response.choices[0].message.content
    
    return {
        "type": "reply",
        "content": final_message,
        "timestamp": int(time.time() * 1000)
    }
```

### Step 3: 更新 server.py

**檔案位置：** `/root/openclaw-chat-server/server.py`

#### 對話歷史管理

```python
# 在記憶體維護對話歷史（或用 Redis）
conversation_histories = {}  # {connection_id: [messages]}

@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    conversation_histories[connection_id] = []
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # 取得對話歷史
                history = conversation_histories[connection_id]
                
                # 呼叫 OpenAI（帶 tools）
                result = await send_message_with_tools(
                    message=data["content"],
                    tools=TOOL_DEFINITIONS,  # 從 tools.py 載入
                    conversation_history=history.copy()
                )
                
                if result["type"] == "tool_call":
                    # 通知 Android 執行工具
                    await websocket.send_json(result)
                    
                    # 等待 Android 回傳結果
                    tool_result_data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=30.0
                    )
                    
                    # 送回 OpenAI 取得最終回覆
                    final_reply = await continue_with_tool_result(
                        conversation_history=history,
                        tool_call_id=result["tool_call_id"],
                        tool_name=result["tool_name"],
                        tool_arguments=result["tool_arguments"],
                        tool_result=tool_result_data["content"]
                    )
                    
                    # 更新歷史
                    conversation_histories[connection_id] = history
                    
                    # 送最終回覆給 Android
                    await websocket.send_json(final_reply)
                else:
                    # 直接回覆（不需要 tool）
                    history.append({"role": "user", "content": data["content"]})
                    history.append({"role": "assistant", "content": result["content"]})
                    conversation_histories[connection_id] = history[-20:]  # 保留最近 10 輪
                    
                    await websocket.send_json(result)
            
            elif data["type"] == "tool_result":
                # 已在上面的流程中處理
                pass
    
    except WebSocketDisconnect:
        # 清理歷史
        if connection_id in conversation_histories:
            del conversation_histories[connection_id]
```

### Step 4: 更新環境變數

**檔案：** `/root/openclaw-chat-server/.env`

```bash
# OpenAI API Key（必須）
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenClaw token（保留，供其他功能用）
OPENCLAW_CHAT_OPENCLAW_TOKEN=834d03bc292e68d0550e654176a986c90e2edca1074948bd
```

### Step 5: 重啟 chat-server

```bash
systemctl restart openclaw-chat
# 或
sudo systemctl restart openclaw-chat
```

---

## 測試步驟

### 1. 測試一般對話（不觸發 tool）

在 Android App 裡送：
```
「今天天氣如何」
```

預期：
- AI 正常回覆文字
- 不會觸發任何 tool

### 2. 測試 tool calling（播放音樂）

在 Android App 裡送：
```
「幫我播放音樂」
```

預期流程：
1. Server 收到 → 送給 OpenAI
2. OpenAI 回傳 `tool_call: play_music`
3. Server 通知 Android 執行 `play_music`
4. Android 播放音樂並回報 `"Music started"`
5. Server 送回 OpenAI
6. OpenAI 回覆「好的，已經幫你播放音樂了！」
7. Android 顯示最終訊息

### 3. 測試其他工具

- 「幫我拍照」→ `take_photo`
- 「打開 YouTube」→ `open_app(app_name="YouTube")`
- 「導航到台北車站」→ `open_navigation(destination="台北車站")`
- 「停止音樂」→ `stop_music`

---

## OpenAI Function Calling 格式

### Tools 定義（OpenAI 格式）

```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "take_photo",
            "description": "Take a photo using the device camera",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Start playing music",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_music",
            "description": "Stop playing music",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_navigation",
            "description": "Open Google Maps navigation to a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "The destination address or place name"
                    }
                },
                "required": ["destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application on the device",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name or package name of the app to open"
                    }
                },
                "required": ["app_name"]
            }
        }
    }
]
```

---

## 模型選擇

推薦模型（都支援 Function Calling）：

| 模型 | 特點 | 成本 |
|------|------|------|
| `gpt-4o` | 最新、最快、最便宜 | 低 💰 |
| `gpt-4o-mini` | 超便宜、速度快 | 超低 💰 |
| `gpt-4-turbo-preview` | 穩定、功能完整 | 中 💰💰 |
| `gpt-4` | 最強但貴 | 高 💰💰💰 |

**建議：先用 `gpt-4o-mini` 測試（最便宜）**

---

## 費用估算

### GPT-4o-mini 費用（最便宜）
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

### 使用場景估算
假設每次對話：
- Input: 500 tokens（包含歷史 + tools 定義）
- Output: 100 tokens（回覆）

**成本：** 約 $0.0001 / 次對話  
**1000 次對話：** 約 $0.10（10 台幣）

---

## 優勢

✅ **100% 確定支援 Function Calling**  
✅ **文件完整、社群龐大**  
✅ **流量控管清楚**  
✅ **費用透明（比 Anthropic 便宜）**  
✅ **gpt-4o-mini 超便宜**  

---

## 下一步

小八可以開始實作了：

1. ✅ 申請 OpenAI API Key
2. 📝 修改 `bridge.py`（加入 OpenAI client）
3. 📝 修改 `server.py`（加入對話歷史管理）
4. 📦 安裝 `pip install openai`
5. 🔄 重啟 chat-server
6. 🧪 測試 Function Calling

需要我幫忙準備其他資料嗎？
