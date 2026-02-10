# 2026-02-10 上午 — OpenClaw WebSocket v2 修正 + 版本控管

## 摘要

小八修正 Button 6 (OpenClaw AI) WebSocket 連線問題，並建立 GitHub 版本控管。

## 完成項目

### 1. 同步小Linda對話
- 讀取 ai-task-tracker 最新資料
- 小Linda 已準備好：WebSocket 測試成功資料、Kotlin 範例、Python 測試腳本
- 架構：Android → ws://157.180.126.133:8200/chat → chat-server → OpenClaw Gateway

### 2. WebSocket 連線測試（從 Windows）
- Python 測試全部通過：連線、中英文對話、多輪對話、斷線重連、Health check
- 伺服器正常運行

### 3. 修正 Button 6 WebSocket 連線（v2）

#### 發現的問題
1. **XML layout 預設 URL 錯誤** — port 18789（Gateway 直連，不可達）應為 8200
2. **SharedPreferences 殘留舊 URL** — 舊版 app 存的 18789 會被新版讀到
3. **Error 訊息解析錯誤** — Server 的 error 在 `error` 欄位，client 卻讀 `content`
4. **無自動重連機制**
5. **WebSocket 和 SDK 狀態互相覆蓋** — 只有一行狀態列

#### 修改的檔案
1. `activity_openclaw_chat.xml` — 修正預設 URL 18789→8200，新增雙行狀態列（WS + SDK）+ 版本標示
2. `OpenClawClient.kt` — 自動重連（最多5次指數退避）、修正 error 解析、新增 connectTimeout
3. `OpenClawChatActivity.kt` — SharedPreferences 遷移（自動修正舊 URL）、分離 WS/SDK 狀態顯示、版本標示 BUILD_VERSION

### 4. Build + 安裝到手機
- 用 Android Studio 內建 JDK 21 + Gradle 命令列 build
- ADB 安裝到小米 Mix 2S（裝置 216e810c）
- 用戶確認 v2 版運作正常

### 5. GitHub 版本控管
- 安裝 gh CLI（winget install GitHub.cli）
- 登入 GitHub（smilenccc）
- 建立 private repo：https://github.com/smilenccc/android-audioconnect-openclaw
- 初始 commit：10bfc0e（977 files, v2）
- .gitignore 排除 build/、.gradle/、signing files

### 6. 效能測試
- 連線建立：822ms
- 平均回應時間：5.2 秒（AI 推理為主）
- 最快：3.6s（簡單數學）
- 最慢：8.4s（翻譯）

## 版本控管規則
- 每次修改後在 Button 6 頁面標示版本號（v2, v3...）
- 確認可用後才 commit + push
- Repo: smilenccc/android-audioconnect-openclaw (private)

## Build 指令（備忘）
```bash
cd src/
JAVA_HOME="/c/Program Files/Android/Android Studio/jbr" ./gradlew :sample:assembleDebug
adb install -r sample/build/outputs/apk/debug/*.apk
```
