#!/usr/bin/env node
/**
 * Amazon 訂單管理 API Server (Render)
 * 提供動態 API 讓網頁直接新增/刪除訂單
 */

import express from 'express';
import cors from 'cors';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 10003;

// 訂單資料檔案
const ORDERS_FILE = path.join(__dirname, 'orders.json');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// 讀取訂單資料
async function loadOrders() {
    try {
        const data = await fs.readFile(ORDERS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        // 如果檔案不存在，建立預設結構
        return { orders: [], lastUpdated: null };
    }
}

// 儲存訂單資料
async function saveOrders(ordersData) {
    ordersData.lastUpdated = new Date().toISOString();
    await fs.writeFile(ORDERS_FILE, JSON.stringify(ordersData, null, 2), 'utf-8');
}

// API 路由

// 取得所有訂單
app.get('/api/orders', async (req, res) => {
    try {
        const data = await loadOrders();
        res.json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 新增訂單
app.post('/api/orders', async (req, res) => {
    try {
        const { orderNumber, trackingNumber, carrier, productName } = req.body;
        
        // 驗證必填欄位
        if (!orderNumber || !trackingNumber) {
            return res.status(400).json({
                success: false,
                error: '訂單號和追蹤號為必填欄位'
            });
        }
        
        const data = await loadOrders();
        
        // 檢查是否已存在
        const exists = data.orders.some(o => o.orderNumber === orderNumber);
        if (exists) {
            return res.status(400).json({
                success: false,
                error: '訂單已存在'
            });
        }
        
        // 生成新 ID
        const newId = data.orders.length > 0 
            ? Math.max(...data.orders.map(o => o.id)) + 1 
            : 1;
        
        // 建立新訂單
        const newOrder = {
            id: newId,
            orderNumber,
            trackingNumber,
            carrier: carrier || 'Unknown',
            productName: productName || '',
            status: 'pending',
            currentLocation: '未知',
            destination: '台中市大里區',
            addedAt: new Date().toISOString(),
            lastUpdate: new Date().toISOString()
        };
        
        data.orders.push(newOrder);
        await saveOrders(data);
        
        res.json({
            success: true,
            order: newOrder,
            message: `✅ 訂單已新增：${orderNumber}`
        });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 更新訂單狀態
app.put('/api/orders/:id', async (req, res) => {
    try {
        const orderId = parseInt(req.params.id);
        const { status, currentLocation } = req.body;
        
        const data = await loadOrders();
        const order = data.orders.find(o => o.id === orderId);
        
        if (!order) {
            return res.status(404).json({
                success: false,
                error: '訂單不存在'
            });
        }
        
        if (status) order.status = status;
        if (currentLocation) order.currentLocation = currentLocation;
        order.lastUpdate = new Date().toISOString();
        
        await saveOrders(data);
        
        res.json({
            success: true,
            order,
            message: '✅ 訂單已更新'
        });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 刪除訂單
app.delete('/api/orders/:id', async (req, res) => {
    try {
        const orderId = parseInt(req.params.id);
        
        const data = await loadOrders();
        const originalLength = data.orders.length;
        
        data.orders = data.orders.filter(o => o.id !== orderId);
        
        if (data.orders.length === originalLength) {
            return res.status(404).json({
                success: false,
                error: '訂單不存在'
            });
        }
        
        await saveOrders(data);
        
        res.json({
            success: true,
            message: `✅ 訂單已刪除 (ID: ${orderId})`
        });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// 健康檢查
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'Amazon Order Tracker',
        timestamp: new Date().toISOString()
    });
});

// 啟動服務
app.listen(PORT, () => {
    console.log('📦 Amazon 訂單管理 API Server');
    console.log('='.repeat(50));
    console.log(`📍 Port: ${PORT}`);
    console.log(`🔗 API: /api/orders`);
    console.log('='.repeat(50));
});
