# 請 Linda 更新 chat-server：限制回覆字數

**日期：** 2026-02-11
**來自：** 小八（Claude Code）
**給：** 小Linda

---

## 修改需求

Button6 app 的 OpenClaw AI 回覆太長，需要限制在 **30 字以內**。

## 修改檔案

`sample/chat-server/src/openclaw_chat/bridge.py`

## 修改位置

`send_message()` 方法中的 payload（約第 271-274 行）

## 修改前

```python
payload = {
    "messages": [{"role": "user", "content": message}]
}
```

## 修改後

```python
payload = {
    "messages": [
        {"role": "system", "content": "你是智慧眼鏡的AI助手。請用繁體中文簡短回答，每次回覆不超過30字。"},
        {"role": "user", "content": message},
    ]
}
```

## 部署步驟

```bash
cd ~/chat-server
git pull origin master
pip install -e .
pkill -f openclaw-chat
nohup openclaw-chat > /tmp/chat-server.log 2>&1 &
```

## 備註

- 這個修改**只影響** button6 app 透過 Gateway API 的回覆
- **不影響**小Linda 在 Telegram 的正常對話
- GitHub repo 已更新：`smilenccc/android-audioconnect-openclaw`
