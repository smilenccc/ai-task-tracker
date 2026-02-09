#!/usr/bin/env node
/**
 * Coupang 訂單資料匯入工具
 *
 * 使用方式：
 *   1. 在 Chrome 開啟 Coupang 訂單頁面
 *   2. 按 F12 開啟 DevTools → Console
 *   3. 貼上 console-script.js 的內容並按 Enter
 *   4. 腳本會自動下載 coupang-orders.json
 *   5. 把下載的檔案放到這個資料夾
 *   6. 執行 node extract-orders.mjs 來合併資料
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { categorize } from './config.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const inputFiles = [
  resolve(__dirname, 'coupang-orders.json'),
  resolve(process.env.USERPROFILE || '', 'Downloads', 'coupang-orders.json'),
];

const outputPath = resolve(__dirname, '..', 'purchases.json');

function loadExisting() {
  if (!existsSync(outputPath)) {
    return {
      meta: { lastUpdated: new Date().toISOString(), totalSpent: 0, currency: 'TWD', source: 'coupang-scraper' },
      purchases: [],
    };
  }
  try {
    return JSON.parse(readFileSync(outputPath, 'utf-8'));
  } catch {
    return {
      meta: { lastUpdated: new Date().toISOString(), totalSpent: 0, currency: 'TWD', source: 'coupang-scraper' },
      purchases: [],
    };
  }
}

function main() {
  // Find the input file
  let inputPath = null;
  for (const p of inputFiles) {
    if (existsSync(p)) {
      inputPath = p;
      break;
    }
  }

  if (!inputPath) {
    console.log('❌ 找不到 coupang-orders.json');
    console.log('');
    console.log('請先在 Chrome 開啟 Coupang 訂單頁面，');
    console.log('然後按 F12 → Console，貼上以下腳本：');
    console.log('');
    console.log('  console-script.js 的內容');
    console.log('');
    console.log('下載的檔案應在：');
    inputFiles.forEach(p => console.log(`  - ${p}`));
    process.exit(1);
  }

  console.log(`📂 讀取: ${inputPath}`);
  const rawOrders = JSON.parse(readFileSync(inputPath, 'utf-8'));

  if (!Array.isArray(rawOrders) || rawOrders.length === 0) {
    console.log('❌ 檔案中沒有訂單資料');
    process.exit(1);
  }

  console.log(`📦 讀取到 ${rawOrders.length} 筆訂單`);

  // Process and categorize
  const processed = rawOrders.map(order => ({
    orderId: order.orderId || `coupang-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    date: order.date || '',
    name: order.name || '',
    price: typeof order.price === 'number' ? order.price : parseFloat(String(order.price).replace(/[^\d.]/g, '')) || 0,
    currency: 'TWD',
    quantity: order.quantity || 1,
    category: categorize(order.name || ''),
    status: order.status || '',
    imageUrl: order.imageUrl || '',
    productLink: order.productLink || '',
    source: 'coupang',
    scrapedAt: new Date().toISOString(),
  }));

  // Merge with existing
  const existing = loadExisting();
  const existingIds = new Set(existing.purchases.map(p => p.orderId));
  let added = 0;

  for (const order of processed) {
    if (!existingIds.has(order.orderId)) {
      existing.purchases.push(order);
      existingIds.add(order.orderId);
      added++;
    }
  }

  existing.purchases.sort((a, b) => new Date(b.date) - new Date(a.date));
  existing.meta.lastUpdated = new Date().toISOString();
  existing.meta.totalSpent = existing.purchases.reduce((s, p) => s + (p.price || 0), 0);
  existing.meta.totalItems = existing.purchases.length;

  writeFileSync(outputPath, JSON.stringify(existing, null, 2), 'utf-8');
  console.log(`✅ 合併完成：新增 ${added} 筆，略過 ${processed.length - added} 筆重複`);
  console.log(`📊 共 ${existing.purchases.length} 筆訂單，總消費 NT$${existing.meta.totalSpent.toLocaleString()}`);
  console.log(`💾 已儲存至 ${outputPath}`);
}

main();
