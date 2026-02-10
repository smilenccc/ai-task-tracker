# 部署 Tool Calling 到 Hetzner chat-server

## 背景

小八已經完成 tool calling 的程式碼，推到 GitHub（`smilenccc/android-audioconnect-openclaw`）。
現在需要在 Hetzner 上更新 chat-server 讓新功能生效。

## 架構說明

```
一般對話 → OpenClaw (Claude AI)    ← 跟以前一樣，不變
控制手機 → OpenAI API (gpt-4o-mini) ← 新增
```

每次收到訊息：
1. 先問 OpenAI「這句話需不需要控制手機？」
2. 需要 → OpenAI 處理 tool flow（拍照、播放音樂等）
3. 不需要 → 轉給 OpenClaw 回覆（跟以前一模一樣）

## 改動的檔案（已在 GitHub）

| 檔案 | 改了什麼 |
|------|---------|
| `bridge.py` | 新增 OpenAI client，用於 tool calling |
| `server.py` | 雙 AI 路由：OpenAI 判斷 tool → OpenClaw 處理一般對話 |
| `config.py` | 新增 `openai_api_key` 和 `openai_model` 設定 |
| `pyproject.toml` | 新增 `openai` 套件依賴 |
| `tools.py` | 5 個 tool 定義（take_photo, play_music, stop_music, open_navigation, open_app） |
| `models.py` | 新增 tool_call / tool_result 訊息類型 |

## 部署步驟

### Step 1: 拉最新程式碼

```bash
cd /root/openclaw-chat-server
git pull
```

> 如果目錄位置不同，請調整路徑。repo 是 `smilenccc/android-audioconnect-openclaw`，chat-server 在 `sample/chat-server/` 下面。

### Step 2: 安裝新的 Python 套件

```bash
source venv/bin/activate
pip install openai
```

### Step 3: 設定環境變數

在 `.env` 檔案中加入：

```bash
OPENCLAW_CHAT_OPENAI_API_KEY=<請跟小八拿 OpenAI API Key>
OPENCLAW_CHAT_OPENAI_MODEL=gpt-4o-mini
```

可以用指令加入：
```bash
echo 'OPENCLAW_CHAT_OPENAI_API_KEY=<請跟小八拿 OpenAI API Key>' >> .env
echo 'OPENCLAW_CHAT_OPENAI_MODEL=gpt-4o-mini' >> .env
```

### Step 4: 重啟 chat-server

```bash
systemctl restart openclaw-chat
```

### Step 5: 確認服務正常

```bash
systemctl status openclaw-chat
```

應該要看到 `active (running)`。

如果有錯誤，看 log：
```bash
journalctl -u openclaw-chat -n 50 --no-pager
```

## 驗證方式

部署完成後，小八會用 Android App 測試：

- "今天天氣如何" → 應走 OpenClaw，正常回覆文字
- "幫我播放音樂" → 應走 OpenAI，觸發 play_music tool
- "打開 YouTube" → 應走 OpenAI，觸發 open_app tool

## 注意事項

- OpenClaw Gateway **不需要改動**，保持原樣
- 原本的一般對話功能完全不受影響
- OpenAI 費用：gpt-4o-mini 非常便宜，1000 次對話約 $0.10
- OpenAI API Key 的流量上限建議設 $10/月（https://platform.openai.com/settings/organization/limits）
