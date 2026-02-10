import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5567;

// CORS 設定
app.use(cors());
app.use(express.json());

// 靜態檔案
app.use(express.static(__dirname));

// API: 取得交易記錄
app.get('/api/transactions', (req, res) => {
    try {
        const data = fs.readFileSync(path.join(__dirname, 'transactions.json'), 'utf8');
        res.json(JSON.parse(data));
    } catch (error) {
        console.error('Error reading transactions:', error);
        res.status(500).json({ error: 'Failed to load transactions' });
    }
});

// 健康檢查
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'credit-card-dashboard' });
});

// 首頁
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`💳 信用卡消費統計系統運行中`);
    console.log(`🌐 http://localhost:${PORT}`);
});
