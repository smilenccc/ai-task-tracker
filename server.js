import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 8100;

// 提供靜態檔案
app.use(express.static(__dirname));

// 主頁
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// 任務 API（如果需要）
app.get('/api/tasks', (req, res) => {
  res.sendFile(path.join(__dirname, 'tasks.json'));
});

// 購物記錄 API
app.get('/api/purchases', (req, res) => {
  res.sendFile(path.join(__dirname, 'purchases.json'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Task Tracker 運行中: http://0.0.0.0:${PORT}`);
  console.log(`📊 主頁: http://157.180.126.133:${PORT}`);
});
