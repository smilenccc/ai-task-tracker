/**
 * OpenClaw WebSocket 整合範例 (Kotlin)
 * 
 * 依賴: implementation("com.squareup.okhttp3:okhttp:4.12.0")
 */

import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class OpenClawWebSocketClient {
    
    private val serverUrl = "ws://157.180.126.133:8200/chat"
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    // 連線狀態回調
    interface ConnectionListener {
        fun onConnected()
        fun onMessage(message: String)
        fun onError(error: String)
        fun onDisconnected()
    }
    
    private var listener: ConnectionListener? = null
    
    /**
     * 連接到 OpenClaw
     */
    fun connect(listener: ConnectionListener) {
        this.listener = listener
        
        val request = Request.Builder()
            .url(serverUrl)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            
            override fun onOpen(webSocket: WebSocket, response: Response) {
                println("✅ WebSocket 連線成功")
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    val type = json.getString("type")
                    val content = json.optString("content", "")
                    val error = json.optString("error", null)
                    
                    when (type) {
                        "connected" -> {
                            println("📡 收到連線確認: $content")
                            listener.onConnected()
                        }
                        "reply" -> {
                            println("📥 收到 AI 回覆: $content")
                            listener.onMessage(content)
                        }
                        "error" -> {
                            println("⚠️ 收到錯誤: $error")
                            listener.onError(error ?: "未知錯誤")
                        }
                        else -> {
                            println("📨 未知訊息類型: $type")
                        }
                    }
                } catch (e: Exception) {
                    println("❌ JSON 解析錯誤: ${e.message}")
                    listener.onError("訊息格式錯誤")
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                println("❌ 連線失敗: ${t.message}")
                listener.onError(t.message ?: "連線失敗")
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                println("🔌 連線關閉中: $reason")
                webSocket.close(1000, null)
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                println("🔌 連線已關閉")
                listener.onDisconnected()
            }
        })
    }
    
    /**
     * 發送訊息給 AI
     */
    fun sendMessage(userMessage: String): Boolean {
        return try {
            val json = JSONObject().apply {
                put("type", "message")
                put("content", userMessage)
            }
            
            println("📤 發送訊息: $userMessage")
            webSocket?.send(json.toString()) ?: false
        } catch (e: Exception) {
            println("❌ 發送失敗: ${e.message}")
            false
        }
    }
    
    /**
     * 斷開連線
     */
    fun disconnect() {
        webSocket?.close(1000, "客戶端主動斷線")
        webSocket = null
    }
    
    /**
     * 檢查連線狀態
     */
    fun isConnected(): Boolean {
        return webSocket != null
    }
}

/**
 * 使用範例
 */
fun main() {
    val client = OpenClawWebSocketClient()
    
    client.connect(object : OpenClawWebSocketClient.ConnectionListener {
        override fun onConnected() {
            println("🎉 已連接到小Linda！")
            // 連線成功後，可以開始發送訊息
            client.sendMessage("你好！我是從 Android 連線的。")
        }
        
        override fun onMessage(message: String) {
            println("收到回覆: $message")
            // 顯示 AI 回覆在 UI 上
        }
        
        override fun onError(error: String) {
            println("發生錯誤: $error")
            // 顯示錯誤訊息
        }
        
        override fun onDisconnected() {
            println("連線已斷開")
        }
    })
    
    // 讓程式保持運行以接收訊息
    Thread.sleep(60000)
    
    // 斷開連線
    client.disconnect()
}
