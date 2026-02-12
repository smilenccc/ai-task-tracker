#!/usr/bin/env node
/**
 * Coupang 消費分析 — 本地 Server
 *
 * 功能：
 *   1. 提供分析儀表板網頁 (http://localhost:5566)
 *   2. 接收 Tampermonkey 腳本自動傳送的訂單資料 (POST /api/orders)
 *   3. 自動合併、去重、分類、儲存到 purchases.json
 *
 * 啟動：
 *   node coupang/server.mjs
 */

import express from 'express';
import cors from 'cors';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, '..');

const PORT = process.env.PORT || 8101;
const PURCHASES_PATH = resolve(ROOT, 'purchases.json');

// ── 分類規則（與 config.mjs 同步） ──────────────────
const CATEGORIES = {
  '食品/飲料': ['咖啡','茶','水','飲料','零食','餅乾','巧克力','糖果','米','麵','醬','油','鹽','糖','醋','食品','堅果','牛奶','優格','果汁','啤酒','酒','泡麵','罐頭','調味','雞','豬','牛','魚','蝦','肉','蔬菜','水果','麵包','蛋糕','冰淇淋','起司','奶油','軟糖','糖'],
  '3C/電子': ['手機','耳機','充電','電池','線材','USB','HDMI','鍵盤','滑鼠','iPad','iPhone','Samsung','平板','記憶卡','SD','SSD','硬碟','螢幕','音響','喇叭','AirPods','Apple','電腦','筆電','Switch','PS5','相機','鏡頭','GoPro','投影','路由器','WiFi'],
  '日用品/清潔': ['衛生紙','面紙','洗衣','洗碗','清潔','垃圾袋','牙刷','牙膏','洗髮','沐浴','肥皂','洗手','拖把','掃把','刷子','海綿','漂白','除臭','柔軟','芳香','殺菌','消毒','抹布','馬桶'],
  '美妝/保養': ['面膜','化妝','口紅','眼影','粉底','防曬','乳液','精華','卸妝','保濕','面霜','護手','香水','指甲','眉筆','睫毛','腮紅'],
  '服飾/配件': ['衣','褲','裙','外套','帽','襪','鞋','包包','背包','皮夾','手錶','項鍊','耳環','圍巾','手套','皮帶','太陽眼鏡'],
  '居家/傢俱': ['枕頭','棉被','床單','毛巾','窗簾','地毯','收納','置物','掛鉤','燈','蠟燭','花瓶','碗','盤','杯','筷','鍋','刀','砧板'],
  '健康/運動': ['維他命','保健','營養','蛋白','益生菌','口罩','OK繃','體溫','血壓','瑜珈','啞鈴','跑步','運動','健身'],
  '母嬰/寵物': ['尿布','奶瓶','奶嘴','嬰兒','寶寶','貓','狗','飼料','貓砂','寵物','紙尿褲','幫寶適','Pampers'],
  '書籍/文具': ['書','筆','筆記本','文具','膠帶','剪刀','便利貼','資料夾','計算機'],
};

function categorize(name) {
  const lower = name.toLowerCase();
  for (const [cat, keywords] of Object.entries(CATEGORIES)) {
    if (keywords.some(kw => lower.includes(kw.toLowerCase()))) return cat;
  }
  return '其他';
}

// ── 資料操作 ────────────────────────────────────────
function loadPurchases() {
  if (!existsSync(PURCHASES_PATH)) {
    return { meta: { lastUpdated: new Date().toISOString(), totalSpent: 0, totalItems: 0, currency: 'TWD', source: 'coupang-scraper' }, purchases: [] };
  }
  try {
    return JSON.parse(readFileSync(PURCHASES_PATH, 'utf-8'));
  } catch {
    return { meta: { lastUpdated: new Date().toISOString(), totalSpent: 0, totalItems: 0, currency: 'TWD', source: 'coupang-scraper' }, purchases: [] };
  }
}

function savePurchases(data) {
  data.meta.lastUpdated = new Date().toISOString();
  data.meta.totalSpent = data.purchases.reduce((s, p) => s + (p.price || 0), 0);
  data.meta.totalItems = data.purchases.length;
  writeFileSync(PURCHASES_PATH, JSON.stringify(data, null, 2), 'utf-8');
  
  // 自動推送到 GitHub
  try {
    execSync('git add purchases.json', { cwd: ROOT });
    execSync(`git commit -m "Coupang: 更新購物資料 (${data.meta.totalItems} 筆, NT$${data.meta.totalSpent})"`, { cwd: ROOT });
    execSync('git push origin main', { cwd: ROOT });
    console.log('✅ 已推送到 GitHub');
  } catch (e) {
    console.warn('⚠️ Git 推送失敗:', e.message);
  }
}

// ── Server ──────────────────────────────────────────
const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' }));

// 靜態檔案：分析網站
app.use(express.static(resolve(__dirname)));
// 也提供 purchases.json
app.get('/purchases.json', (req, res) => {
  res.json(loadPurchases());
});

// API：接收訂單資料
app.post('/api/orders', (req, res) => {
  const orders = req.body;

  if (!Array.isArray(orders) || orders.length === 0) {
    return res.status(400).json({ error: 'Expected non-empty array of orders' });
  }

  console.log(`📦 收到 ${orders.length} 筆訂單`);
  console.log('詳細資料：', JSON.stringify(orders, null, 2));

  const existing = loadPurchases();
  const existingMap = new Map(existing.purchases.map(p => [`${p.name}|${p.date}|${p.price}`, p]));
  let added = 0;
  let updated = 0;

  for (const order of orders) {
    const key = `${order.name}|${order.date}|${order.price}`;
    const existingItem = existingMap.get(key);
    
    // 如果存在且狀態不同，更新狀態
    if (existingItem) {
      if (existingItem.status !== order.status) {
        existingItem.status = order.status;
        existingItem.updatedAt = new Date().toISOString();
        updated++;
        console.log(`🔄 更新狀態: ${order.name.substring(0, 30)}... (${existingItem.status})`);
      }
      continue;
    }

    existing.purchases.push({
      orderId: order.orderId || `coupang-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      date: order.date || '',
      name: order.name || '',
      price: typeof order.price === 'number' ? order.price : parseInt(String(order.price).replace(/[^\d]/g, '')) || 0,
      currency: 'TWD',
      quantity: order.quantity || 1,
      category: categorize(order.name || ''),
      status: order.status || '',
      imageUrl: order.imageUrl || '',
      productLink: order.productLink || '',
      source: 'coupang',
      scrapedAt: new Date().toISOString(),
    });
    existingMap.set(key, existing.purchases[existing.purchases.length - 1]);
    added++;
  }

  existing.purchases.sort((a, b) => new Date(b.date) - new Date(a.date));
  savePurchases(existing);

  console.log(`✅ 新增 ${added} 筆，更新 ${updated} 筆，略過 ${orders.length - added - updated} 筆`);
  console.log(`📊 共 ${existing.purchases.length} 筆，NT$${existing.meta.totalSpent.toLocaleString()}`);

  res.json({ success: true, added, updated, total: existing.purchases.length });
});

// API：取得統計
app.get('/api/stats', (req, res) => {
  const data = loadPurchases();
  res.json(data.meta);
});

app.listen(PORT, () => {
  console.log('');
  console.log('🛒 Coupang 消費分析 Server 啟動');
  console.log(`📊 儀表板：http://localhost:${PORT}/index.html`);
  console.log(`📡 API：   http://localhost:${PORT}/api/orders`);
  console.log('');
  console.log('Tampermonkey 腳本會自動將訂單資料傳送到這裡');
  console.log('按 Ctrl+C 停止 server');
  console.log('');
});
