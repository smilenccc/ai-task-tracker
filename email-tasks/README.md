# 📧 郵件交辦任務安全系統

## 🔐 安全機制

### 三層防護

1. **發件人白名單**
   - 只接受 `smilenccc@gmail.com` 的郵件
   - 其他郵件一律拒絕

2. **工作範圍限制**
   - ✅ **允許**：dashboard、網頁、統計、信用卡、資料、圖表、報表、分析
   - ❌ **禁止**：修改系統、刪除檔案、修改資料庫、執行指令、修改防火牆

3. **Telegram 確認機制**
   - 收到郵件後，Linda 會在 Telegram 向你確認
   - 只有你確認後才執行
   - 可以拒絕任何看起來可疑的任務

---

## 📋 運作流程

```
1. 📧 你從 smilenccc@gmail.com 寄郵件
   ↓
2. 🔍 系統檢查發件人（白名單）
   ↓
3. 🛡️ 系統檢查任務內容（安全性）
   ↓
4. 💬 Linda 在 Telegram 向你確認
   ↓
5. ✅ 你確認後，Linda 開始執行
   ↓
6. 📊 結果顯示在 Dashboard
```

---

## ✅ 允許的工作類型

### Dashboard 相關
- 建立新的 dashboard 頁面
- 製作資料視覺化圖表
- 設計網頁界面
- 統計資料展示

### 資料分析
- 信用卡消費統計
- 購物記錄分析
- 資料查詢和匯總
- 生成報表

### 範例郵件

**主旨**：請製作信用卡本月消費統計

**內容**：
```
請幫我建立一個信用卡消費統計 dashboard，顯示：
1. 本月消費總額
2. 分類別消費（餐飲、購物、交通等）
3. 與上月比較
4. 圖表視覺化
```

**處理流程**：
1. ✅ 發件人驗證通過（smilenccc@gmail.com）
2. ✅ 內容檢查通過（包含「統計」「信用卡」「dashboard」）
3. 💬 Linda 在 Telegram 問你：「收到郵件任務，要執行嗎？」
4. ✅ 你回覆確認
5. 🚀 Linda 開始建立 dashboard
6. 📊 完成後顯示在網站上

---

## ❌ 禁止的工作類型

### 系統修改
```
❌ 請幫我修改防火牆規則
❌ 請執行 sudo rm -rf /
❌ 請修改系統設定
❌ 請刪除舊檔案
```

### 資料庫操作
```
❌ 請修改資料庫
❌ 請刪除 tasks.json
❌ 請更新用戶資料
```

**這些請求會被自動拒絕，不會送到 Telegram 確認。**

---

## 🌐 查看任務狀態

訪問：`https://smilenccc.github.io/ai-task-tracker/email-tasks/`

可以看到：
- 📊 任務統計（待確認、已完成、已拒絕）
- 📋 所有任務列表
- ⏰ 時間軸
- ✅ 執行結果

---

## 🛠️ 系統架構

### 檔案結構
```
email-tasks/
├── email_handler.py    # Python 後端處理器
├── config.json         # 配置（白名單、規則）
├── tasks.json          # 任務記錄
├── index.html          # Dashboard 網頁
└── README.md           # 本文件
```

### 資料格式

**config.json**
```json
{
  "allowed_senders": ["smilenccc@gmail.com"],
  "allowed_actions": ["dashboard", "統計", "信用卡", ...],
  "forbidden_actions": ["修改系統", "刪除檔案", ...]
}
```

**tasks.json**
```json
{
  "tasks": [
    {
      "id": 1,
      "sender": "smilenccc@gmail.com",
      "subject": "請製作信用卡統計",
      "content": "...",
      "status": "completed",
      "receivedAt": "2026-02-11T08:00:00",
      "confirmedAt": "2026-02-11T08:05:00",
      "completedAt": "2026-02-11T08:30:00",
      "result": "已建立 dashboard: ..."
    }
  ]
}
```

---

## 🔧 管理

### 新增白名單郵件地址

編輯 `config.json`：
```json
{
  "allowed_senders": [
    "smilenccc@gmail.com",
    "another@example.com"
  ]
}
```

### 新增允許的關鍵字

編輯 `config.json`：
```json
{
  "allowed_actions": [
    "dashboard",
    "統計",
    "新關鍵字"
  ]
}
```

### 測試安全機制

```bash
cd /root/.openclaw/workspace/task-tracker/email-tasks
python3 email_handler.py
```

---

## 📊 任務狀態說明

- **⏳ 待確認** (`pending_confirmation`) - 收到郵件，等待 Telegram 確認
- **✅ 已確認** (`confirmed`) - 已確認，準備執行
- **🎉 已完成** (`completed`) - 已完成，有結果
- **❌ 已拒絕** (`rejected`) - 被拒絕（不安全或主動拒絕）

---

## ⚠️ 安全提醒

1. **永遠不要**在郵件中包含：
   - 密碼或敏感資訊
   - 系統指令
   - 刪除操作

2. **如果收到可疑的 Telegram 確認請求**：
   - 檢查郵件來源
   - 檢查任務內容
   - 有疑問就拒絕

3. **定期檢查任務記錄**：
   - 訪問 Dashboard 查看所有任務
   - 確認沒有異常任務

---

**建立日期**：2026-02-11  
**維護者**：Linda (AI Assistant)  
**安全等級**：🔒🔒🔒 三層防護
