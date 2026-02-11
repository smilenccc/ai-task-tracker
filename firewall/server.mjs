#!/usr/bin/env node
/**
 * 防火牆白名單查看系統 (Render)
 * - 2FA 登入保護
 * - 唯讀查看白名單和規則
 */

import express from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import path from 'path';
import { fileURLToPath } from 'url';
import { authenticator } from 'otplib';
import fetch from 'node-fetch';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 10002;

// 配置
const TOTP_SECRET = process.env.TOTP_SECRET || 'U3KQHZMQ4UMNVTZYXTPGJ2AGLBRPZR5L';
const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://157.180.126.133:5001';
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'linda-firewall-webhook-secret-2026';

// 會話管理
const sessions = new Map();
const SESSION_TIMEOUT = 60 * 60 * 1000; // 1 小時

// Middleware
app.use(cors());
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 生成會話 token
function generateSessionToken() {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

// 驗證會話
function verifySession(token) {
    const session = sessions.get(token);
    if (!session) return false;
    
    if (Date.now() > session.expiresAt) {
        sessions.delete(token);
        return false;
    }
    
    return true;
}

// 中間件：檢查是否已登入
function requireAuth(req, res, next) {
    const sessionToken = req.cookies?.sessionToken || req.query.session;
    
    if (!verifySession(sessionToken)) {
        return res.redirect('/');
    }
    
    next();
}

// 登入頁面
app.get('/', (req, res) => {
    const sessionToken = req.cookies?.sessionToken;
    
    // 如果已登入，跳轉到白名單頁面
    if (verifySession(sessionToken)) {
        return res.redirect('/whitelist');
    }
    
    res.send(`
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 防火牆管理 - 2FA 登入</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft JhengHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.8em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1.1em;
            text-align: center;
            letter-spacing: 0.3em;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-top: 20px;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 8px;
            margin-top: 15px;
            text-align: center;
            display: none;
        }
        .error.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ 防火牆管理</h1>
        <p class="subtitle">請輸入 Authy 驗證碼</p>
        
        <form onsubmit="login(event)">
            <label for="token">6 位數驗證碼</label>
            <input type="text" id="token" maxlength="6" pattern="[0-9]{6}" required autocomplete="off" autofocus>
            <button type="submit">🔓 登入</button>
        </form>
        
        <div class="error" id="error"></div>
    </div>

    <script>
        async function login(event) {
            event.preventDefault();
            const token = document.getElementById('token').value;
            const errorDiv = document.getElementById('error');
            
            try {
                const response = await fetch('/api/auth/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.cookie = 'sessionToken=' + data.sessionToken + '; path=/; max-age=3600';
                    window.location.href = '/whitelist';
                } else {
                    errorDiv.textContent = data.error;
                    errorDiv.classList.add('show');
                    setTimeout(() => errorDiv.classList.remove('show'), 3000);
                }
            } catch (error) {
                errorDiv.textContent = '連線錯誤：' + error.message;
                errorDiv.classList.add('show');
            }
        }
    </script>
</body>
</html>
    `);
});

// 2FA 驗證 API
app.post('/api/auth/verify', (req, res) => {
    const { token } = req.body;
    
    if (!token || token.length !== 6) {
        return res.json({
            success: false,
            error: '請輸入完整的 6 位數驗證碼'
        });
    }
    
    // 驗證 TOTP token
    const isValid = authenticator.verify({ token, secret: TOTP_SECRET });
    
    if (isValid) {
        // 建立會話
        const sessionToken = generateSessionToken();
        sessions.set(sessionToken, {
            createdAt: Date.now(),
            expiresAt: Date.now() + SESSION_TIMEOUT
        });
        
        res.json({
            success: true,
            message: '✅ 驗證成功',
            sessionToken
        });
    } else {
        res.json({
            success: false,
            error: '❌ 驗證碼無效或已過期'
        });
    }
});

// 白名單查看頁面（需要登入）
app.get('/whitelist', requireAuth, (req, res) => {
    res.send(`
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ 防火牆白名單</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft JhengHei', Arial, sans-serif;
            background: #1a1d23;
            color: #e5e7eb;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        h1 { color: #fff; font-size: 2em; }
        .btn {
            background: #ef4444;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            text-decoration: none;
            font-weight: 600;
            border: none;
            cursor: pointer;
        }
        .section {
            background: #0f1115;
            border: 1px solid #2d3138;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 1.3em;
            font-weight: 600;
            color: #fff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .refresh-btn {
            margin-left: auto;
            background: #d50c2d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85em;
        }
        .ip-list { display: grid; gap: 10px; }
        .ip-item {
            background: #1a1d23;
            border: 1px solid #2d3138;
            border-radius: 6px;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .ip-address {
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
            color: #10b981;
            font-weight: 600;
        }
        .ip-status { color: #6b7280; font-size: 0.9em; }
        .rules-box {
            background: #1a1d23;
            border: 1px solid #2d3138;
            border-radius: 6px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #e5e7eb;
            overflow-x: auto;
            white-space: pre;
            max-height: 400px;
            overflow-y: auto;
        }
        .loading, .error, .empty {
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }
        .error { color: #ef4444; }
        .info-box {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            color: #3b82f6;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🛡️ 防火牆白名單</h1>
                <p style="color: #9ca3af; margin-top: 5px;">唯讀模式 - 查看白名單與規則</p>
            </div>
            <button class="btn" onclick="logout()">🚪 登出</button>
        </header>

        <div class="info-box">
            💡 這是唯讀頁面。要修改白名單，請透過 Telegram 告訴 Linda。
        </div>

        <div class="section">
            <div class="section-title">
                📋 白名單 IP
                <button class="refresh-btn" onclick="loadWhitelist()">🔄 重新整理</button>
            </div>
            <div class="ip-list" id="whitelistDiv">
                <div class="loading">載入中...</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">
                📜 防火牆規則
                <button class="refresh-btn" onclick="loadRules()">🔄 重新整理</button>
            </div>
            <div class="rules-box" id="rulesDiv">
                <div class="loading">載入中...</div>
            </div>
        </div>
    </div>

    <script>
        async function loadWhitelist() {
            const whitelistDiv = document.getElementById('whitelistDiv');
            whitelistDiv.innerHTML = '<div class="loading">載入中...</div>';

            try {
                const response = await fetch('/api/firewall/whitelist');

                const data = await response.json();

                if (data.success && data.ips) {
                    if (data.ips.length === 0) {
                        whitelistDiv.innerHTML = '<div class="empty">目前沒有白名單 IP</div>';
                        return;
                    }

                    whitelistDiv.innerHTML = data.ips.map(ip => \`
                        <div class="ip-item">
                            <span class="ip-address">\${ip}</span>
                            <span class="ip-status">✓ 允許</span>
                        </div>
                    \`).join('');
                } else {
                    whitelistDiv.innerHTML = '<div class="error">載入失敗：' + (data.error || '未知錯誤') + '</div>';
                }
            } catch (error) {
                whitelistDiv.innerHTML = '<div class="error">連線錯誤：' + error.message + '</div>';
            }
        }

        async function loadRules() {
            const rulesDiv = document.getElementById('rulesDiv');
            rulesDiv.innerHTML = '<div class="loading">載入中...</div>';

            try {
                const response = await fetch('/api/firewall/rules');

                const data = await response.json();

                if (data.success && data.rules) {
                    rulesDiv.textContent = data.rules;
                } else {
                    rulesDiv.innerHTML = '<div class="error">載入失敗：' + (data.error || '未知錯誤') + '</div>';
                }
            } catch (error) {
                rulesDiv.innerHTML = '<div class="error">連線錯誤：' + error.message + '</div>';
            }
        }

        function logout() {
            if (confirm('確定要登出嗎？')) {
                document.cookie = 'sessionToken=; path=/; max-age=0';
                window.location.href = '/';
            }
        }

        loadWhitelist();
        loadRules();
        setInterval(() => {
            loadWhitelist();
            loadRules();
        }, 30000);
    </script>
</body>
</html>
    `);
});

// 登出
app.get('/logout', (req, res) => {
    res.send('<script>document.cookie="sessionToken=; path=/; max-age=0"; window.location.href="/";</script>');
});

// API 代理：取得白名單
app.get('/api/firewall/whitelist', async (req, res) => {
    try {
        const response = await fetch(`${WEBHOOK_URL}/webhook/firewall/whitelist`, {
            headers: { 'X-API-Key': WEBHOOK_SECRET }
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// API 代理：取得規則
app.get('/api/firewall/rules', async (req, res) => {
    try {
        const response = await fetch(`${WEBHOOK_URL}/webhook/firewall/rules`, {
            headers: { 'X-API-Key': WEBHOOK_SECRET }
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

// 健康檢查
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'Firewall Whitelist Viewer',
        timestamp: new Date().toISOString()
    });
});

// 啟動服務
app.listen(PORT, () => {
    console.log('🛡️ 防火牆白名單查看系統');
    console.log('='.repeat(50));
    console.log(`📍 Port: ${PORT}`);
    console.log(`🔐 2FA Secret: ${TOTP_SECRET.substring(0, 8)}...`);
    console.log(`🔗 Webhook: ${WEBHOOK_URL}`);
    console.log('='.repeat(50));
});
