/**
 * Coupang 訂單提取腳本
 *
 * 使用方式：
 *   1. 在 Chrome 登入 Coupang → 進入「訂單紀錄」頁面
 *   2. 按 F12 打開 DevTools → 切到 Console
 *   3. 全選複製這個檔案的內容，貼到 Console 按 Enter
 *   4. 腳本會自動提取訂單並下載 JSON 檔
 *   5. 如果有多頁訂單，會自動翻頁（或提示手動翻頁）
 */

(async () => {
  console.log('🛒 Coupang 訂單提取開始...');

  const allOrders = [];
  let pageNum = 1;

  async function extractCurrentPage() {
    const orders = [];

    // Strategy 1: Try to find order elements in the DOM
    // Common selectors for Coupang order items
    const possibleSelectors = [
      '[class*="order-item"]',
      '[class*="orderItem"]',
      '[class*="order-list"] > div',
      '[class*="order-list"] > li',
      '[class*="orderList"] > div',
      '[class*="orderList"] > li',
      '.order-card',
      '[class*="OrderCard"]',
      '[class*="order_item"]',
      '[class*="purchaseItem"]',
      '[data-order-id]',
      '[data-orderid]',
    ];

    let orderElements = [];
    for (const sel of possibleSelectors) {
      const els = document.querySelectorAll(sel);
      if (els.length > 0) {
        orderElements = Array.from(els);
        console.log(`📋 找到 ${els.length} 筆訂單 (選擇器: ${sel})`);
        break;
      }
    }

    if (orderElements.length > 0) {
      for (const el of orderElements) {
        try {
          const order = extractFromElement(el);
          if (order.name || order.price) {
            orders.push(order);
          }
        } catch (e) {
          console.warn('提取失敗:', e);
        }
      }
    }

    // Strategy 2: If no structured elements found, try broad text extraction
    if (orders.length === 0) {
      console.log('🔄 嘗試廣泛提取...');

      // Look for any elements that contain order-like data
      const allElements = document.querySelectorAll('div, li, article, section');
      for (const el of allElements) {
        const text = el.innerText || '';
        // Check if this element looks like an order (has date + price pattern)
        const hasDate = /\d{4}[./\-]\d{1,2}[./\-]\d{1,2}/.test(text);
        const hasPrice = /(?:NT\$|＄|\$)\s*[\d,]+/.test(text) || /[\d,]+\s*元/.test(text);

        if (hasDate && hasPrice && text.length < 1000 && text.length > 20) {
          // Check it's not a parent of already-found items
          const childCount = el.querySelectorAll('div, li').length;
          if (childCount < 10) { // Likely a leaf-ish element
            const order = extractFromText(text, el);
            if (order && !orders.some(o => o.orderId === order.orderId)) {
              orders.push(order);
            }
          }
        }
      }
    }

    return orders;
  }

  function extractFromElement(el) {
    const getText = (selectors) => {
      for (const sel of selectors.split(', ')) {
        const found = el.querySelector(sel);
        if (found) return found.textContent.trim();
      }
      return '';
    };

    const getAttr = (selectors, attr) => {
      for (const sel of selectors.split(', ')) {
        const found = el.querySelector(sel);
        if (found) return found.getAttribute(attr) || '';
      }
      return '';
    };

    const orderId = getText('[class*="order-id"], [class*="orderId"], [class*="order-number"], [class*="orderNumber"]')
      || el.getAttribute('data-order-id') || el.getAttribute('data-orderid')
      || `coupang-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

    const dateText = getText('[class*="order-date"], [class*="orderDate"], [class*="date"], time');
    const name = getText('[class*="product-name"], [class*="productName"], [class*="item-name"], [class*="itemName"], [class*="name"]');
    const priceText = getText('[class*="price"], [class*="total"], [class*="amount"]');
    const status = getText('[class*="status"], [class*="delivery"], [class*="shipping"]');
    const imageUrl = getAttr('[class*="product"] img, [class*="item"] img, img', 'src');
    const productLink = getAttr('[class*="product"] a, [class*="item"] a, a[href*="products"]', 'href');

    let date = '';
    const dateMatch = dateText.match(/(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})/);
    if (dateMatch) {
      date = `${dateMatch[1]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[3].padStart(2, '0')}`;
    }

    const price = parsePrice(priceText);

    return {
      orderId: orderId.replace(/[^a-zA-Z0-9\-]/g, '') || `coupang-${Date.now()}`,
      date,
      name,
      price,
      status,
      imageUrl,
      productLink: productLink ? new URL(productLink, location.origin).href : '',
    };
  }

  function extractFromText(text, el) {
    const dateMatch = text.match(/(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})/);
    const priceMatch = text.match(/(?:NT\$|＄|\$)\s*([\d,]+)/) || text.match(/([\d,]+)\s*元/);

    if (!dateMatch) return null;

    const date = `${dateMatch[1]}-${dateMatch[2].padStart(2, '0')}-${dateMatch[3].padStart(2, '0')}`;
    const price = priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0;

    // Try to find the product name — look for text that's not the date or price
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    let name = '';
    for (const line of lines) {
      if (!line.match(/^\d{4}[./\-]/) && !line.match(/^(?:NT\$|＄|\$)/) &&
          !line.match(/^\d+$/) && line.length > 2 && line.length < 200 &&
          !line.match(/^(已完成|配送中|已取消|處理中|訂單|查看|退貨|退款)/)) {
        name = line;
        break;
      }
    }

    const img = el.querySelector('img');
    const link = el.querySelector('a[href*="product"], a[href*="item"]');

    return {
      orderId: `coupang-${date}-${Math.random().toString(36).slice(2, 7)}`,
      date,
      name,
      price,
      status: '',
      imageUrl: img ? img.src : '',
      productLink: link ? link.href : '',
    };
  }

  function parsePrice(text) {
    if (!text) return 0;
    const cleaned = text.replace(/[^\d.]/g, '');
    return parseFloat(cleaned) || 0;
  }

  // Extract from current page
  const orders = await extractCurrentPage();
  allOrders.push(...orders);
  console.log(`📄 第 ${pageNum} 頁: ${orders.length} 筆訂單`);

  // Check for pagination
  const nextBtns = document.querySelectorAll('[class*="next"], [class*="pagination"] a:last-child, button[aria-label="next"], a[aria-label="next"]');
  let hasNext = false;
  for (const btn of nextBtns) {
    if (!btn.disabled && !btn.classList.toString().includes('disabled')) {
      hasNext = true;
      break;
    }
  }

  if (hasNext) {
    console.log('⚠️  檢測到有下一頁！');
    console.log('   如要爬取所有頁面，請手動翻到下一頁後重新執行此腳本');
    console.log('   或稍後合併多次提取的結果');
  }

  // Download results
  if (allOrders.length > 0) {
    const blob = new Blob([JSON.stringify(allOrders, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'coupang-orders.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    console.log(`✅ 已下載 ${allOrders.length} 筆訂單至 coupang-orders.json`);
  } else {
    console.log('❌ 未找到任何訂單');
    console.log('💡 提示：');
    console.log('   - 確認你在「訂單紀錄」頁面');
    console.log('   - 確認頁面已完全載入');
    console.log('   - 嘗試在 Console 輸入以下指令查看頁面結構：');
    console.log('     document.querySelectorAll("[class*=order]")');

    // Debug: show page structure
    console.log('\n📊 頁面結構分析：');
    const orderLike = document.querySelectorAll('[class*="order"], [class*="Order"]');
    console.log(`   含 "order" 的元素: ${orderLike.length} 個`);
    orderLike.forEach((el, i) => {
      if (i < 10) console.log(`   [${i}] <${el.tagName.toLowerCase()} class="${el.className.slice(0, 80)}">`);
    });
  }
})();
