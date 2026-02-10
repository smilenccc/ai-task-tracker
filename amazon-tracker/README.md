# 📦 Amazon 包裹追蹤系統

自動追蹤 Amazon.de 訂單物流狀態

## 🎯 功能特色

- ✅ 自動監控 Gmail 中的 Amazon 物流更新郵件
- ✅ 支援 Amazon Logistics 自營物流系統
- ✅ 實時追蹤包裹位置和狀態
- ✅ 重要狀態變更自動通知（Telegram）
- ✅ 視覺化追蹤頁面，整合到個人 Dashboard

## 📋 目前追蹤的訂單

### 訂單 #303-0977485-2042700
- **追蹤號：** AXIXPPL001333550
- **物流商：** Amazon Logistics
- **寄送路線：** 德國 → 台灣
- **狀態：** 運送中

## 🔗 快速連結

- [追蹤頁面](https://smilenccc.github.io/ai-task-tracker/amazon-tracker/) - 視覺化追蹤介面
- [Amazon 直接追蹤](https://track.amazon.de/AXIXPPL001333550) - 官方追蹤頁面
- [訂單詳情](https://www.amazon.de/gp/css/shiptrack/view.html?orderID=303-0977485-2042700) - Amazon 訂單頁面

## 🤖 自動監控

Linda 會每小時執行以下任務：

1. 檢查 Gmail 中的 Amazon 郵件
2. 自動提取物流更新資訊
3. 偵測重要狀態變更：
   - 📤 已出貨 (Shipped)
   - 🚚 運送中 (In Transit)
   - 🏠 配送中 (Out for Delivery)
   - ✅ 已送達 (Delivered)
4. 重要更新會透過 Telegram 主動通知

## 📊 物流狀態記錄

所有追蹤記錄會保存在 `tracking_updates.json`，包含：
- 郵件主旨
- 收到時間
- 狀態變更
- 寄件來源

## 🔧 手動查詢

如需手動查詢物流狀態：

```bash
cd /root/.openclaw/workspace/amazon-tracker
python3 monitor_package.py
```

## 📝 技術細節

- **監控頻率：** 每小時（透過 HEARTBEAT.md）
- **資料來源：** linda.openclaw@gmail.com
- **憑證位置：** `/root/.openclaw/workspace/.amazon-credentials`
- **追蹤記錄：** `tracking_updates.json`

---

**建立時間：** 2026-02-10  
**最後更新：** 2026-02-10 03:45 UTC
