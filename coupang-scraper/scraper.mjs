#!/usr/bin/env node
/**
 * Coupang 酷澎台灣 — 訂單歷史爬蟲 v2
 *
 * 改進重點：
 *   1. 使用 playwright-extra + stealth 插件繞過 Akamai CDN 偵測
 *   2. 借用用戶真實 Chrome Profile（已登入的 session）
 *   3. 模擬真實瀏覽器行為（滑鼠移動、隨機延遲、滾動）
 *   4. Headed 模式讓用戶可手動處理 CAPTCHA
 *
 * 使用方式：
 *   npm run scrape            # headed 模式（預設，推薦）
 *   npm run scrape:headless   # headless 模式（需要 stealth 夠強才行）
 *
 * Windows:
 *   set HEADED=1 && node scraper.mjs
 */

import { chromium } from 'playwright-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { config as loadEnv } from 'dotenv';
import { homedir } from 'os';

import { URLS, SELECTORS, SCRAPER_CONFIG, categorize } from './config.mjs';

// Apply stealth plugin
chromium.use(StealthPlugin());

// __dirname for ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env from project root
loadEnv({ path: resolve(__dirname, '..', '.env') });

const COUPANG_EMAIL = process.env.COUPANG_EMAIL;
const COUPANG_PASSWORD = process.env.COUPANG_PASSWORD;

if (!COUPANG_EMAIL || !COUPANG_PASSWORD || COUPANG_EMAIL === 'your_email@example.com') {
  console.error('❌ 請先在 .env 檔案中設定 COUPANG_EMAIL 和 COUPANG_PASSWORD');
  process.exit(1);
}

// ── Helpers ─────────────────────────────────────────────

function randomDelay(min = SCRAPER_CONFIG.delay.min, max = SCRAPER_CONFIG.delay.max) {
  return new Promise((r) => setTimeout(r, min + Math.random() * (max - min)));
}

function log(msg) {
  const ts = new Date().toLocaleTimeString('zh-TW', { hour12: false });
  console.log(`[${ts}] ${msg}`);
}

function loadExistingPurchases() {
  const filePath = resolve(__dirname, SCRAPER_CONFIG.outputPath);
  if (!existsSync(filePath)) {
    return {
      meta: {
        lastUpdated: new Date().toISOString(),
        totalSpent: 0,
        currency: 'TWD',
        source: 'coupang-scraper',
      },
      purchases: [],
    };
  }
  try {
    return JSON.parse(readFileSync(filePath, 'utf-8'));
  } catch {
    log('⚠️  purchases.json 解析失敗，將建立新檔案');
    return {
      meta: {
        lastUpdated: new Date().toISOString(),
        totalSpent: 0,
        currency: 'TWD',
        source: 'coupang-scraper',
      },
      purchases: [],
    };
  }
}

function savePurchases(data) {
  const filePath = resolve(__dirname, SCRAPER_CONFIG.outputPath);
  data.meta.lastUpdated = new Date().toISOString();
  data.meta.totalSpent = data.purchases.reduce((sum, p) => sum + (p.price || 0), 0);
  data.meta.totalItems = data.purchases.length;
  writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
  log(`✅ 已儲存 ${data.purchases.length} 筆訂單至 purchases.json`);
}

function mergePurchases(existing, newOrders) {
  const existingIds = new Set(existing.purchases.map((p) => p.orderId));
  let added = 0;
  for (const order of newOrders) {
    if (!existingIds.has(order.orderId)) {
      existing.purchases.push(order);
      existingIds.add(order.orderId);
      added++;
    }
  }
  existing.purchases.sort((a, b) => new Date(b.date) - new Date(a.date));
  log(`📊 合併完成：新增 ${added} 筆，略過 ${newOrders.length - added} 筆重複`);
  return existing;
}

function parsePrice(priceText) {
  if (!priceText) return 0;
  const cleaned = priceText.replace(/[^\d.]/g, '');
  return parseFloat(cleaned) || 0;
}

// ── Human-like behavior ─────────────────────────────────

async function humanScroll(page) {
  const scrolls = 2 + Math.floor(Math.random() * 3);
  for (let i = 0; i < scrolls; i++) {
    const distance = 200 + Math.floor(Math.random() * 400);
    await page.mouse.wheel(0, distance);
    await randomDelay(300, 800);
  }
}

async function humanMouseMove(page) {
  const x = 100 + Math.floor(Math.random() * 800);
  const y = 100 + Math.floor(Math.random() * 500);
  await page.mouse.move(x, y, { steps: 5 + Math.floor(Math.random() * 10) });
}

async function humanType(locator, text) {
  await locator.click();
  await randomDelay(200, 500);
  // Clear existing content
  await locator.fill('');
  // Type character by character with random delays
  for (const char of text) {
    await locator.pressSequentially(char, { delay: 50 + Math.random() * 100 });
  }
}

// ── Auth ────────────────────────────────────────────────

function getAuthDir() {
  const dir = resolve(__dirname, '..', '.auth');
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  return dir;
}

// Find user's real Chrome profile path
function findChromeProfilePath() {
  const home = homedir();
  const possiblePaths = [
    // Windows
    join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data'),
    // macOS
    join(home, 'Library', 'Application Support', 'Google', 'Chrome'),
    // Linux
    join(home, '.config', 'google-chrome'),
  ];

  for (const p of possiblePaths) {
    if (existsSync(p)) {
      log(`📂 找到 Chrome Profile: ${p}`);
      return p;
    }
  }
  return null;
}

// ── Browser & Login ─────────────────────────────────────

async function launchBrowser() {
  log('🚀 啟動你的 Chrome 瀏覽器（使用真實 Profile）...');

  // Use the user's REAL Chrome profile
  const chromeProfilePath = findChromeProfilePath();
  if (!chromeProfilePath) {
    log('❌ 找不到 Chrome Profile。請確認已安裝 Google Chrome');
    throw new Error('CHROME_NOT_FOUND');
  }

  log(`📂 Chrome Profile: ${chromeProfilePath}`);

  const context = await chromium.launchPersistentContext(chromeProfilePath, {
    channel: 'chrome',
    headless: false,
    slowMo: 50,
    viewport: null,  // Use Chrome's default viewport
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-infobars',
      '--profile-directory=Default',
    ],
    ignoreDefaultArgs: ['--enable-automation'],
  });

  const page = context.pages()[0] || await context.newPage();

  return { context, page };
}

async function isLoggedIn(page) {
  try {
    // Visit homepage first to check login state
    await page.goto(URLS.base, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await randomDelay(2000, 3000);
    await humanMouseMove(page);

    const bodyText = await page.locator('body').textContent().catch(() => '');
    if (bodyText.includes('Access Denied') || bodyText.includes('Reference #')) {
      log('⚠️  被 Akamai CDN 擋住了（Access Denied）');
      return false;
    }

    // Check if there's a user-related element (logged in indicator)
    const hasUserInfo = await page
      .locator('[class*="my-coupang"], [class*="user"], [class*="mypage"], [class*="account"], a[href*="mypage"], a[href*="logout"]')
      .first()
      .isVisible({ timeout: 5000 })
      .catch(() => false);

    if (hasUserInfo) {
      log('✅ 首頁偵測到已登入狀態');
      return true;
    }

    // If homepage has login link visible, probably not logged in
    const hasLoginLink = await page
      .locator('a[href*="login"], a:has-text("登入"), button:has-text("登入")')
      .first()
      .isVisible({ timeout: 3000 })
      .catch(() => false);

    return !hasLoginLink;
  } catch {
    return false;
  }
}

async function waitForAccessDeniedClear(page, label = '') {
  const bodyText = await page.locator('body').textContent().catch(() => '');
  if (bodyText.includes('Access Denied') || bodyText.includes('Reference #')) {
    log(`⚠️  ${label}被 Akamai 擋住（Access Denied）`);
    log('   請在瀏覽器中重新整理頁面或手動操作（最多等 3 分鐘）');
    try {
      await page.waitForFunction(
        () => !document.body.textContent.includes('Access Denied'),
        { timeout: 180000 }
      );
      log('✅ Access Denied 已解除');
      return true;
    } catch {
      throw new Error('ACCESS_DENIED');
    }
  }
  return false;
}

async function findLoginPage(page) {
  log('🔍 嘗試找到登入頁面...');

  // Strategy 1: Visit homepage and find login link
  log('📍 訪問首頁尋找登入連結...');
  await page.goto(URLS.base, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await randomDelay(2000, 4000);
  await humanMouseMove(page);
  await waitForAccessDeniedClear(page, '首頁');

  // Try to find and click login link on homepage
  const loginLinkSelectors = SELECTORS.homeLogin.split(', ');
  for (const sel of loginLinkSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 2000 })) {
        const href = await el.getAttribute('href');
        if (href && (href.includes('login') || href.includes('signin'))) {
          log(`✅ 首頁找到登入連結: ${href}`);
          await el.click();
          await page.waitForLoadState('domcontentloaded');
          await randomDelay(1500, 3000);
          log(`📍 登入頁 URL: ${page.url()}`);
          return true;
        }
        // If it's a button/link without href, just click it
        log(`   嘗試點擊: ${sel}`);
        await el.click();
        await page.waitForLoadState('domcontentloaded');
        await randomDelay(1500, 3000);
        if (page.url().includes('login') || page.url().includes('signin')) {
          log(`✅ 導航到登入頁: ${page.url()}`);
          return true;
        }
      }
    } catch {
      // Try next
    }
  }

  // Strategy 2: Try known login URL candidates
  log('🔄 首頁未找到登入連結，嘗試已知 URL...');
  for (const url of URLS.loginCandidates) {
    try {
      log(`   嘗試: ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await randomDelay(1500, 2500);

      const bodyText = await page.locator('body').textContent().catch(() => '');
      // Check if page has login form (not 404 or Access Denied)
      if (!bodyText.includes('找不到頁面') && !bodyText.includes('404') && !bodyText.includes('Not Found')) {
        await waitForAccessDeniedClear(page, '登入頁');
        const hasInput = await page.locator('input[type="email"], input[type="text"], input[name="email"], input[name="username"]')
          .first().isVisible({ timeout: 3000 }).catch(() => false);
        if (hasInput) {
          log(`✅ 找到登入頁: ${url}`);
          return true;
        }
      }
    } catch {
      // Try next URL
    }
  }

  return false;
}

async function login(page) {
  log('🔐 開始登入流程...');

  const foundLogin = await findLoginPage(page);

  if (!foundLogin) {
    log('⚠️  無法自動找到登入頁面');
    log('   請在瀏覽器中手動導航到 Coupang 登入頁並登入');
    log('⏳ 等待手動登入完成（最多 5 分鐘）...');
    try {
      await page.waitForURL(
        (url) => {
          const u = url.toString();
          return u.includes('coupang') && !u.includes('login') && !u.includes('signin');
        },
        { timeout: 300000 }
      );
      log('✅ 手動登入成功');
      return;
    } catch {
      throw new Error('MANUAL_LOGIN_TIMEOUT');
    }
  }

  await humanMouseMove(page);
  log(`📍 登入頁: ${page.url()}`);

  // Try each possible email selector
  const emailSelectors = SELECTORS.login.emailInput.split(', ');
  let emailFilled = false;
  for (const sel of emailSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 3000 })) {
        await humanType(el, COUPANG_EMAIL);
        emailFilled = true;
        log('✅ 已填入 Email');
        break;
      }
    } catch {
      // Try next selector
    }
  }

  if (!emailFilled) {
    const inputs = page.locator('input[type="text"], input[type="email"]');
    const count = await inputs.count();
    for (let i = 0; i < count; i++) {
      if (await inputs.nth(i).isVisible()) {
        await humanType(inputs.nth(i), COUPANG_EMAIL);
        emailFilled = true;
        log('✅ 已填入 Email（fallback 選擇器）');
        break;
      }
    }
  }

  await randomDelay(500, 1200);

  // Try each possible password selector
  const pwSelectors = SELECTORS.login.passwordInput.split(', ');
  let pwFilled = false;
  for (const sel of pwSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 3000 })) {
        await humanType(el, COUPANG_PASSWORD);
        pwFilled = true;
        log('✅ 已填入密碼');
        break;
      }
    } catch {
      // Try next selector
    }
  }

  if (!pwFilled) {
    const inputs = page.locator('input[type="password"]');
    const count = await inputs.count();
    for (let i = 0; i < count; i++) {
      if (await inputs.nth(i).isVisible()) {
        await humanType(inputs.nth(i), COUPANG_PASSWORD);
        pwFilled = true;
        log('✅ 已填入密碼（fallback 選擇器）');
        break;
      }
    }
  }

  if (!emailFilled || !pwFilled) {
    log('⚠️  找不到登入欄位。切換到手動模式...');
    log('   請在瀏覽器中手動登入 Coupang');
    log(`   目前頁面 URL: ${page.url()}`);
    const screenshotPath = resolve(__dirname, '..', 'debug-login.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    log(`   已儲存截圖至 ${screenshotPath}`);

    // Wait for user to manually login
    log('⏳ 等待手動登入完成（最多 5 分鐘）...');
    try {
      await page.waitForURL(
        (url) => url.toString().includes('coupang') && !url.toString().includes('login'),
        { timeout: 300000 }
      );
      log('✅ 手動登入成功');
      return;
    } catch {
      throw new Error('MANUAL_LOGIN_TIMEOUT');
    }
  }

  await randomDelay(500, 1000);
  await humanMouseMove(page);

  // Click submit
  const submitSelectors = SELECTORS.login.submitButton.split(', ');
  let submitted = false;
  for (const sel of submitSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 3000 })) {
        await humanMouseMove(page);
        await randomDelay(200, 500);
        await el.click();
        submitted = true;
        log('✅ 已點擊登入按鈕');
        break;
      }
    } catch {
      // Try next
    }
  }

  if (!submitted) {
    await page.keyboard.press('Enter');
    log('✅ 已按 Enter 送出登入');
  }

  // Wait for navigation after login
  log('⏳ 等待登入完成...');
  await page.waitForTimeout(SCRAPER_CONFIG.delay.afterLogin);

  // Check if CAPTCHA or 2FA appeared
  const currentUrl = page.url();
  if (currentUrl.includes('captcha') || currentUrl.includes('challenge') || currentUrl.includes('verify')) {
    log('⚠️  偵測到驗證碼/二步驟驗證');
    log('   請在瀏覽器中手動完成驗證（最多等 3 分鐘）');
    try {
      await page.waitForURL(
        (url) => !url.toString().includes('captcha') && !url.toString().includes('challenge'),
        { timeout: 180000 }
      );
      log('✅ 驗證完成');
    } catch {
      throw new Error('CAPTCHA_TIMEOUT');
    }
  }

  // Check login success
  if (page.url().includes('login') || page.url().includes('signin')) {
    log('⚠️  自動登入可能失敗，等待手動登入...');
    try {
      await page.waitForURL(
        (url) => !url.toString().includes('login') && !url.toString().includes('signin'),
        { timeout: 180000 }
      );
      log('✅ 登入成功');
    } catch {
      log('❌ 登入逾時');
      const screenshotPath = resolve(__dirname, '..', 'debug-login-fail.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      throw new Error('LOGIN_FAILED');
    }
  }

  log('💾 Session 已儲存（persistent context）');
}

// ── Order Scraping ──────────────────────────────────────

async function scrapeOrdersFromPage(page) {
  const orders = [];

  // Wait for page to fully render
  await randomDelay(1000, 2000);
  await humanScroll(page);
  await randomDelay(500, 1000);

  // Strategy 1: Try to find order items via DOM
  const orderSelectors = SELECTORS.orders.orderItem.split(', ');
  let orderElements = null;

  for (const sel of orderSelectors) {
    try {
      const els = page.locator(sel);
      const count = await els.count();
      if (count > 0) {
        orderElements = els;
        log(`📋 找到 ${count} 筆訂單（選擇器: ${sel}）`);
        break;
      }
    } catch {
      // Try next
    }
  }

  if (!orderElements || (await orderElements.count()) === 0) {
    log('⚠️  DOM 策略未找到訂單，嘗試通用提取...');
    return await scrapeOrdersFallback(page);
  }

  const count = await orderElements.count();
  for (let i = 0; i < count; i++) {
    try {
      const el = orderElements.nth(i);
      const order = await extractOrderData(el);
      if (order && order.orderId) {
        orders.push(order);
      }
    } catch (err) {
      log(`⚠️  第 ${i + 1} 筆訂單提取失敗: ${err.message}`);
    }
  }

  return orders;
}

async function extractOrderData(element) {
  const getText = async (selectorStr) => {
    const selectors = selectorStr.split(', ');
    for (const sel of selectors) {
      try {
        const el = element.locator(sel).first();
        if (await el.isVisible({ timeout: 500 })) {
          return (await el.textContent())?.trim() || '';
        }
      } catch {
        // Try next
      }
    }
    return '';
  };

  const getAttr = async (selectorStr, attr) => {
    const selectors = selectorStr.split(', ');
    for (const sel of selectors) {
      try {
        const el = element.locator(sel).first();
        return (await el.getAttribute(attr)) || '';
      } catch {
        // Try next
      }
    }
    return '';
  };

  const orderId = (await getText(SELECTORS.orders.orderId)) || `coupang-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const dateText = await getText(SELECTORS.orders.orderDate);
  const productName = await getText(SELECTORS.orders.productName);
  const priceText = await getText(SELECTORS.orders.productPrice);
  const imageUrl = await getAttr(SELECTORS.orders.productImage, 'src');
  const productLink = await getAttr(SELECTORS.orders.productLink, 'href');
  const quantity = parseInt(await getText(SELECTORS.orders.quantity)) || 1;
  const status = await getText(SELECTORS.orders.orderStatus);

  // Parse date
  let date = '';
  if (dateText) {
    const dateMatch = dateText.match(/(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})/);
    if (dateMatch) {
      date = `${dateMatch[1]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[3].padStart(2, '0')}`;
    } else {
      date = dateText;
    }
  }

  const price = parsePrice(priceText);
  const category = categorize(productName);

  return {
    orderId: orderId.replace(/[^a-zA-Z0-9\-]/g, ''),
    date,
    name: productName,
    price,
    currency: 'TWD',
    quantity,
    category,
    status,
    imageUrl,
    productLink: productLink ? new URL(productLink, URLS.base).href : '',
    source: 'coupang',
    scrapedAt: new Date().toISOString(),
  };
}

async function scrapeOrdersFallback(page) {
  log('🔄 使用 fallback 策略提取訂單...');
  const orders = [];

  try {
    // Look for JSON-LD or other structured data
    const jsonLdScripts = await page.locator('script[type="application/ld+json"]').all();
    for (const script of jsonLdScripts) {
      try {
        const json = JSON.parse(await script.textContent());
        if (json['@type'] === 'Order' || json.orderNumber) {
          orders.push({
            orderId: json.orderNumber || json.identifier || `coupang-${Date.now()}`,
            date: json.orderDate || '',
            name: json.orderedItem?.name || json.name || '',
            price: parseFloat(json.totalPrice || json.price || 0),
            currency: 'TWD',
            quantity: 1,
            category: categorize(json.orderedItem?.name || json.name || ''),
            status: json.orderStatus || '',
            source: 'coupang',
            scrapedAt: new Date().toISOString(),
          });
        }
      } catch {
        // Not valid JSON
      }
    }

    if (orders.length === 0) {
      const screenshotPath = resolve(__dirname, '..', 'debug-orders.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      log(`📸 已儲存訂單頁截圖至 ${screenshotPath}（請確認頁面結構）`);
      log('   請使用 headed 模式觀察頁面，並更新 config.mjs 中的選擇器');
    }
  } catch (err) {
    log(`❌ Fallback 策略失敗: ${err.message}`);
  }

  return orders;
}

// ── Text-based Order Extraction ─────────────────────────

async function scrapeOrdersFromText(page) {
  const orders = [];
  try {
    // Get the full HTML content and extract order info using patterns
    const html = await page.content();

    // Try to find order data in the page's JavaScript/JSON
    const scriptContents = await page.locator('script').all();
    for (const script of scriptContents) {
      try {
        const text = await script.textContent();
        if (!text) continue;

        // Look for JSON data embedded in scripts
        const jsonMatches = text.match(/\{[^{}]*"order[^{}]*\}/gi) || [];
        for (const match of jsonMatches) {
          try {
            const parsed = JSON.parse(match);
            if (parsed.orderId || parsed.orderNumber || parsed.orderNo) {
              const name = parsed.productName || parsed.name || parsed.itemName || '';
              orders.push({
                orderId: String(parsed.orderId || parsed.orderNumber || parsed.orderNo),
                date: parsed.orderDate || parsed.date || parsed.createdAt || '',
                name,
                price: parsePrice(String(parsed.totalPrice || parsed.price || parsed.amount || 0)),
                currency: 'TWD',
                quantity: parsed.quantity || 1,
                category: categorize(name),
                status: parsed.status || parsed.orderStatus || '',
                source: 'coupang',
                scrapedAt: new Date().toISOString(),
              });
            }
          } catch {
            // Not valid JSON
          }
        }
      } catch {
        // Skip this script
      }
    }

    // Try to extract from visible text using patterns
    if (orders.length === 0) {
      const bodyText = await page.locator('body').innerText().catch(() => '');
      // Look for patterns like: date + product name + price
      // Example: "2025.12.15 商品名稱 NT$1,234"
      const datePattern = /(\d{4}[./\-]\d{1,2}[./\-]\d{1,2})/g;
      const pricePattern = /(?:NT\$|TWD|＄|\$)\s*[\d,]+/g;

      const dates = bodyText.match(datePattern) || [];
      const prices = bodyText.match(pricePattern) || [];

      if (dates.length > 0 && prices.length > 0) {
        log(`   找到 ${dates.length} 個日期和 ${prices.length} 個價格`);
        // This is a rough extraction — better than nothing
        // Detailed structure will need manual selector tuning
      }
    }

    if (orders.length > 0) {
      log(`📝 文字提取找到 ${orders.length} 筆訂單`);
    }
  } catch (err) {
    log(`⚠️  文字提取失敗: ${err.message}`);
  }
  return orders;
}

// ── Network Interception ────────────────────────────────

function setupNetworkInterception(page) {
  const interceptedOrders = [];

  page.on('response', async (response) => {
    const url = response.url();
    if (
      (url.includes('/api/') || url.includes('/order') || url.includes('/purchase')) &&
      response.status() === 200
    ) {
      try {
        const contentType = response.headers()['content-type'] || '';
        if (contentType.includes('json')) {
          const json = await response.json();
          const orders = extractOrdersFromApi(json);
          if (orders.length > 0) {
            log(`🌐 Network 攔截到 ${orders.length} 筆訂單資料`);
            interceptedOrders.push(...orders);
          }
        }
      } catch {
        // Not JSON or parsing failed
      }
    }
  });

  return interceptedOrders;
}

function extractOrdersFromApi(json) {
  const orders = [];

  const candidates = [
    json.data?.orders,
    json.orders,
    json.data?.orderList,
    json.orderList,
    json.result?.orders,
    json.data?.items,
    json.items,
  ].filter(Boolean);

  for (const list of candidates) {
    if (Array.isArray(list)) {
      for (const item of list) {
        const orderId = item.orderId || item.orderNumber || item.id || item.orderNo;
        const name =
          item.productName ||
          item.name ||
          item.itemName ||
          item.items?.[0]?.productName ||
          item.items?.[0]?.name ||
          '';
        const price =
          item.totalPrice ||
          item.price ||
          item.amount ||
          item.paymentAmount ||
          item.items?.[0]?.price ||
          0;

        if (orderId) {
          orders.push({
            orderId: String(orderId),
            date: item.orderDate || item.createdAt || item.date || '',
            name,
            price: typeof price === 'string' ? parsePrice(price) : price,
            currency: 'TWD',
            quantity: item.quantity || item.qty || 1,
            category: categorize(name),
            status: item.status || item.orderStatus || item.deliveryStatus || '',
            source: 'coupang',
            scrapedAt: new Date().toISOString(),
          });
        }
      }
    }
  }

  return orders;
}

// ── Pagination ──────────────────────────────────────────

async function hasNextPage(page) {
  const nextSelectors = SELECTORS.orders.nextPage.split(', ');
  for (const sel of nextSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 2000 })) {
        const isDisabled =
          (await el.getAttribute('disabled')) !== null ||
          (await el.getAttribute('class'))?.includes('disabled') ||
          (await el.getAttribute('aria-disabled')) === 'true';
        if (!isDisabled) return sel;
      }
    } catch {
      // Try next
    }
  }
  return null;
}

async function goToNextPage(page, selector) {
  await humanMouseMove(page);
  await randomDelay(300, 600);
  await page.locator(selector).first().click();
  await randomDelay(SCRAPER_CONFIG.delay.betweenPages, SCRAPER_CONFIG.delay.betweenPages + 1500);
  await page.waitForLoadState('domcontentloaded');
}

// ── Main ────────────────────────────────────────────────

async function main() {
  // Default to headed mode (recommended for Coupang)
  if (!process.env.HEADLESS) {
    process.env.HEADED = '1';
  }

  log('🛒 Coupang 酷澎訂單爬蟲 v2 啟動');
  log('   ✨ 使用 playwright-extra + stealth 插件');
  log('   模式: 半自動（腳本開瀏覽器 + 攔截資料，用戶手動導航）');
  log('');

  let context, page;

  try {
    ({ context, page } = await launchBrowser());

    // Setup network interception (captures API responses in background)
    const interceptedOrders = setupNetworkInterception(page);

    // Navigate to Coupang homepage
    log('📍 導航到 Coupang 首頁...');
    await page.goto(URLS.base, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await randomDelay(2000, 3000);

    // Check for Access Denied on homepage
    const homeBody = await page.locator('body').textContent().catch(() => '');
    if (homeBody.includes('Access Denied')) {
      log('⚠️  首頁被 Akamai 擋住了');
      log('   請在瀏覽器中按 F5 重新整理');
      log('⏳ 等待...');
      await page.waitForFunction(
        () => !document.body.textContent.includes('Access Denied'),
        { timeout: 300000 }
      );
    }

    log('');
    log('═══════════════════════════════════════════════');
    log('  📋 請在瀏覽器中執行以下步驟：');
    log('');
    log('  1. 如果未登入，請先登入 Coupang');
    log('  2. 點擊右上角「我的酷澎」→「訂單紀錄」');
    log('     或直接在網址列輸入訂單頁 URL');
    log('  3. 等待訂單列表載入完成');
    log('  4. 腳本會自動偵測並開始爬取');
    log('');
    log('  如果被擋住（Access Denied），請重新整理頁面');
    log('═══════════════════════════════════════════════');
    log('');
    log('⏳ 等待你導航到訂單頁面（最多 10 分鐘）...');

    // Wait for user to navigate to order page
    // Watch for URL containing 'order' AND page not being a 404/error
    let orderPageReached = false;
    const startTime = Date.now();
    const maxWait = 600000; // 10 minutes

    while (!orderPageReached && (Date.now() - startTime) < maxWait) {
      await page.waitForTimeout(3000); // Poll every 3 seconds

      const currentUrl = page.url();
      const bodyText = await page.locator('body').textContent().catch(() => '');

      // Check if we're on an order page
      if (currentUrl.includes('order') && !bodyText.includes('找不到頁面') &&
          !bodyText.includes('찾을 수 없는') && !bodyText.includes('Access Denied')) {
        // Verify there's actual content (not just an empty frame)
        const hasContent = bodyText.length > 500;
        if (hasContent) {
          log(`✅ 偵測到訂單頁面: ${currentUrl}`);
          orderPageReached = true;
        }
      }
    }

    if (!orderPageReached) {
      log('❌ 等待超時（10 分鐘）。請確認是否成功導航到訂單頁面');
      throw new Error('ORDER_PAGE_TIMEOUT');
    }

    // Wait a bit more for full page render
    await randomDelay(3000, 5000);
    log(`📍 目前頁面: ${page.url()}`);

    // Take a screenshot of the order page for debugging
    const orderScreenshot = resolve(__dirname, '..', 'debug-orders.png');
    await page.screenshot({ path: orderScreenshot, fullPage: true });
    log(`📸 已儲存訂單頁截圖至 ${orderScreenshot}`);

    // Now try to scrape: use both DOM + page content extraction
    const allOrders = [];
    let pageNum = 1;

    while (pageNum <= SCRAPER_CONFIG.maxPages) {
      log(`📄 正在爬取第 ${pageNum} 頁...`);

      // Try DOM-based extraction first
      const pageOrders = await scrapeOrdersFromPage(page);

      // Also try full-page text extraction if DOM extraction got nothing
      if (pageOrders.length === 0) {
        log('🔄 嘗試全頁文字提取...');
        const textOrders = await scrapeOrdersFromText(page);
        pageOrders.push(...textOrders);
      }

      allOrders.push(...pageOrders);
      log(`   本頁取得 ${pageOrders.length} 筆訂單`);

      // Check for next page
      const nextSelector = await hasNextPage(page);
      if (!nextSelector) {
        log('📄 已到達最後一頁');
        break;
      }

      await goToNextPage(page, nextSelector);
      pageNum++;
    }

    // Merge network-intercepted orders
    if (interceptedOrders.length > 0) {
      log(`🌐 合併 Network 攔截的 ${interceptedOrders.length} 筆訂單`);
      allOrders.push(...interceptedOrders);
    }

    // Deduplicate within this run
    const uniqueMap = new Map();
    for (const order of allOrders) {
      if (!uniqueMap.has(order.orderId)) {
        uniqueMap.set(order.orderId, order);
      }
    }
    const uniqueOrders = [...uniqueMap.values()];
    log(`📊 本次共爬取 ${uniqueOrders.length} 筆不重複訂單`);

    // Merge with existing data
    const existing = loadExistingPurchases();
    const merged = mergePurchases(existing, uniqueOrders);
    savePurchases(merged);

    log('🎉 爬蟲完成！');
  } catch (err) {
    log(`❌ 爬蟲錯誤: ${err.message}`);
    if (page) {
      const screenshotPath = resolve(__dirname, '..', 'debug-error.png');
      await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
      log(`   已儲存錯誤截圖至 ${screenshotPath}`);
    }
    process.exit(1);
  } finally {
    if (context) {
      await context.close();
      log('🔒 瀏覽器已關閉');
    }
  }
}

main();
