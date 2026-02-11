#!/usr/bin/env node
/**
 * 防火牆管理前端 Server (Render)
 * 處理 2FA 認證，轉發請求到 VPS Webhook
 */

import express from 'express';
import cors from 'cors';
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
const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://localhost:5001';
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'linda-firewall-webhook-secret-2026';

// 簡易會話管理
const sessions = new Map();
const SESSION_TIMEOUT = 60 * 60 * 1000; // 1 小時

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

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

// API 路由

// 2FA 驗證
app.post('/api/auth/verify', (req, res) => {
    const { token } = req.body;
    
    if (!token || token.length !== 6) {
        return res.status(400).json({
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
        res.status(401).json({
            success: false,
            error: '❌ Token 無效或已過期'
        });
    }
});

// 轉發請求到 VPS Webhook
async function proxyToWebhook(endpoint, method = 'GET', body = null, sessionToken = null) {
    // 驗證會話
    if (!verifySession(sessionToken)) {
        return {
            success: false,
            error: '未授權：會話已過期'
        };
    }
    
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': WEBHOOK_SECRET
            }
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${WEBHOOK_URL}${endpoint}`, options);
        const data = await response.json();
        
        return data;
    } catch (error) {
        console.error('Webhook 錯誤:', error);
        return {
            success: false,
            error: `連線錯誤：${error.message}`
        };
    }
}

// 取得白名單
app.get('/api/firewall/whitelist', async (req, res) => {
    const sessionToken = req.headers.authorization?.replace('Bearer ', '');
    const result = await proxyToWebhook('/webhook/firewall/whitelist', 'GET', null, sessionToken);
    res.json(result);
});

// 新增 IP
app.post('/api/firewall/add', async (req, res) => {
    const sessionToken = req.headers.authorization?.replace('Bearer ', '');
    const result = await proxyToWebhook('/webhook/firewall/add', 'POST', req.body, sessionToken);
    res.json(result);
});

// 移除 IP
app.post('/api/firewall/remove', async (req, res) => {
    const sessionToken = req.headers.authorization?.replace('Bearer ', '');
    const result = await proxyToWebhook('/webhook/firewall/remove', 'POST', req.body, sessionToken);
    res.json(result);
});

// 取得防火牆規則
app.get('/api/firewall/rules', async (req, res) => {
    const sessionToken = req.headers.authorization?.replace('Bearer ', '');
    const result = await proxyToWebhook('/webhook/firewall/rules', 'GET', null, sessionToken);
    res.json(result);
});

// 健康檢查
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'Linda Firewall Frontend',
        webhook: WEBHOOK_URL
    });
});

// 啟動服務
app.listen(PORT, () => {
    console.log('🛡️ Linda 防火牆管理前端');
    console.log('='.repeat(50));
    console.log(`📍 Port: ${PORT}`);
    console.log(`🔗 Webhook URL: ${WEBHOOK_URL}`);
    console.log(`🔐 2FA Secret: ${TOTP_SECRET.substring(0, 8)}...`);
    console.log('='.repeat(50));
});
