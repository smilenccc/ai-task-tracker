# OpenClaw Chat Android App 遷移指南

## 📋 變更概要

**日期**: 2026-02-15  
**原因**: 安全性加固（8200 端口直接暴露風險）  
**變更**: WebSocket 從 `ws://` 改為 `wss://`（透過 Nginx 反向代理）

---

## 🔄 連線方式變更

### 舊配置（已停用）
```
協議: ws://
地址: 157.180.126.133:8200/chat
認證: OpenClaw Token（可能）
加密: ❌ 無加密
```

### 新配置（2026-02-15 起）
```
協議: wss://
地址: smilelinda.duckdns.org/openclaw-chat/chat
認證: Session Cookie（密碼登入）
加密: ✅ TLS/SSL（Let's Encrypt）
```

---

## 🔐 認證機制

### 1. 登入流程

用戶需要先透過網頁登入取得 session：

```
步驟 1: 訪問登入頁面
URL: https://smilelinda.duckdns.org/login
方法: POST
Content-Type: application/x-www-form-urlencoded

Body:
password=你的密碼

步驟 2: 伺服器回傳 Set-Cookie
回應標頭:
Set-Cookie: session=<session_token>; Path=/; HttpOnly

步驟 3: 儲存 Cookie
將 session cookie 儲存在 App 中
```

### 2. WebSocket 連線

使用取得的 session cookie 連接 WebSocket：

```
URL: wss://smilelinda.duckdns.org/openclaw-chat/chat
標頭: Cookie: session=<session_token>
```

---

## 📱 Android 實作建議

### 方案 A: WebView Cookie 共享（推薦）

使用 WebView 登入，然後共享 cookie 給 WebSocket：

```kotlin
// 1. 登入頁面（WebView）
val webView = WebView(context)
webView.settings.javaScriptEnabled = true

CookieManager.getInstance().setAcceptCookie(true)
CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true)

webView.loadUrl("https://smilelinda.duckdns.org/login")

// 2. 登入成功後取得 Cookie
val cookies = CookieManager.getInstance().getCookie("https://smilelinda.duckdns.org")
// cookies 格式: "session=abc123; Path=/"

// 3. 解析 session token
val sessionToken = cookies.split(";")
    .find { it.trim().startsWith("session=") }
    ?.split("=")?.get(1)

// 4. 連接 WebSocket（使用 OkHttp）
val client = OkHttpClient.Builder()
    .cookieJar(WebViewCookieJar()) // 使用 WebView 的 CookieJar
    .build()

val request = Request.Builder()
    .url("wss://smilelinda.duckdns.org/openclaw-chat/chat")
    .addHeader("Cookie", "session=$sessionToken")
    .build()

val webSocket = client.newWebSocket(request, webSocketListener)
```

### 方案 B: 手動 Cookie 管理

```kotlin
// 1. HTTP 登入
suspend fun login(password: String): String? {
    val client = OkHttpClient()
    val formBody = FormBody.Builder()
        .add("password", password)
        .build()
    
    val request = Request.Builder()
        .url("https://smilelinda.duckdns.org/login")
        .post(formBody)
        .build()
    
    return withContext(Dispatchers.IO) {
        val response = client.newCall(request).execute()
        if (response.isSuccessful) {
            // 從回應標頭取得 session cookie
            response.headers("Set-Cookie")
                .find { it.startsWith("session=") }
                ?.split(";")?.get(0)
                ?.split("=")?.get(1)
        } else {
            null
        }
    }
}

// 2. 連接 WebSocket
fun connectWebSocket(sessionToken: String) {
    val client = OkHttpClient()
    val request = Request.Builder()
        .url("wss://smilelinda.duckdns.org/openclaw-chat/chat")
        .addHeader("Cookie", "session=$sessionToken")
        .build()
    
    val listener = object : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            Log.d("WS", "連線成功")
        }
        
        override fun onMessage(webSocket: WebSocket, text: String) {
            Log.d("WS", "收到訊息: $text")
        }
        
        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            Log.e("WS", "連線失敗: ${t.message}")
        }
    }
    
    client.newWebSocket(request, listener)
}
```

### 方案 C: 使用 WebViewCookieJar（最簡單）

```kotlin
// WebViewCookieJar.kt
class WebViewCookieJar : CookieJar {
    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        val cookieManager = CookieManager.getInstance()
        cookies.forEach { cookie ->
            cookieManager.setCookie(url.toString(), cookie.toString())
        }
    }

    override fun loadForRequest(url: HttpUrl): List<Cookie> {
        val cookieManager = CookieManager.getInstance()
        val cookieString = cookieManager.getCookie(url.toString()) ?: return emptyList()
        
        return cookieString.split(";").mapNotNull { cookieStr ->
            Cookie.parse(url, cookieStr.trim())
        }
    }
}

// 使用方式
val client = OkHttpClient.Builder()
    .cookieJar(WebViewCookieJar())
    .build()

// WebView 登入後，WebSocket 會自動帶上 cookie
val request = Request.Builder()
    .url("wss://smilelinda.duckdns.org/openclaw-chat/chat")
    .build()

val webSocket = client.newWebSocket(request, listener)
```

---

## 🔧 需要修改的檔案

### 1. 設定檔 / Constants
```kotlin
// Before
const val WEBSOCKET_URL = "ws://157.180.126.133:8200/chat"

// After
const val WEBSOCKET_URL = "wss://smilelinda.duckdns.org/openclaw-chat/chat"
const val LOGIN_URL = "https://smilelinda.duckdns.org/login"
```

### 2. WebSocket 連線邏輯
- 加入 Cookie 管理
- 處理 HTTPS/WSS 證書驗證
- 加入登入流程

### 3. 使用者介面
- 新增登入畫面（或使用 WebView）
- 儲存/清除 session 的功能
- 登入狀態指示

---

## 🧪 測試步驟

### 1. 測試登入 API

使用 `curl` 或 Postman 測試：

```bash
curl -v -X POST https://smilelinda.duckdns.org/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "password=你的密碼"

# 預期回應:
# HTTP/1.1 200 OK
# Set-Cookie: session=xxxx; Path=/; HttpOnly
# {"success": true}
```

### 2. 測試 WebSocket 連線

使用 `wscat` 測試（需要先取得 session cookie）：

```bash
# 安裝 wscat
npm install -g wscat

# 連接（需要替換 session token）
wscat -c "wss://smilelinda.duckdns.org/openclaw-chat/chat" \
  --header "Cookie: session=你的session_token"
```

### 3. Android App 測試清單

- [ ] 登入功能正常
- [ ] Session cookie 正確儲存
- [ ] WebSocket 連線成功（wss://）
- [ ] 訊息收發正常
- [ ] App 重啟後 session 持續有效
- [ ] Session 過期時能重新登入
- [ ] 網路切換時重連正常
- [ ] SSL 證書驗證通過

---

## 📦 相依套件建議

### Gradle dependencies

```gradle
// OkHttp (WebSocket + HTTP)
implementation 'com.squareup.okhttp3:okhttp:4.12.0'

// 如果需要 JSON 解析
implementation 'com.google.code.gson:gson:2.10.1'

// 如果使用 Kotlin Coroutines
implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
```

---

## ⚠️ 注意事項

### 1. SSL 證書
- 伺服器使用 Let's Encrypt 證書（正式 CA）
- Android 7.0+ 預設信任
- 不需要自定義 `TrustManager`

### 2. Session 管理
- Session 有效期：通常 24 小時（由伺服器設定）
- 過期後需要重新登入
- 建議儲存密碼（加密）以便自動重新登入

### 3. 安全性
- **不要** 在程式碼中寫死密碼
- Session token 要安全儲存（Android Keystore）
- 使用 HTTPS/WSS（已強制）

### 4. 向後相容
- 舊版 App（ws://）已無法連線（防火牆已封鎖 8200）
- 需要強制更新 App

---

## 🐛 故障排除

### 問題 1: WebSocket 連線失敗 (401 Unauthorized)
**原因**: 未提供 session cookie 或 session 已過期  
**解決**: 重新登入取得新的 session

### 問題 2: SSL Handshake Failed
**原因**: Android 版本太舊或證書驗證問題  
**解決**: 
- 確保 Android 5.0+（API 21+）
- 檢查系統時間是否正確

### 問題 3: 連線成功但立即斷開
**原因**: Nginx 認證失敗  
**解決**: 檢查 Cookie 格式和內容是否正確

### 問題 4: 無法登入 (密碼正確但失敗)
**原因**: CSRF 或其他伺服器端限制  
**解決**: 聯繫 Linda 檢查伺服器日誌

---

## 📞 聯繫資訊

如有問題請聯繫：
- **Smile** (主要負責人)
- **Linda** (OpenClaw 管理)

測試環境：
- **正式環境**: https://smilelinda.duckdns.org
- **WebSocket**: wss://smilelinda.duckdns.org/openclaw-chat/chat

---

## 📝 更新日誌

**2026-02-15**
- 初版文件
- 從 `ws://157.180.126.133:8200` 遷移至 `wss://smilelinda.duckdns.org/openclaw-chat/`
- 新增 session 認證機制
- 封鎖 8200 直接訪問

---

**文件版本**: v1.0  
**最後更新**: 2026-02-15  
**作者**: Linda (OpenClaw AI Assistant)
