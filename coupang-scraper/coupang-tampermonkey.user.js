// ==UserScript==
// @name         Coupang 訂單自動提取
// @namespace    https://github.com/smilenccc/ai-task-tracker
// @version      1.1
// @description  自動提取 Coupang 訂單資料並傳送到本地分析 Server
// @author       小八
// @match        https://mc.tw.coupang.com/ssr/desktop/order/*
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @connect      localhost
// @connect      coupang-dashboard.onrender.com
// ==/UserScript==

(function() {
  'use strict';

  const SERVER_URL = 'http://localhost:5566/api/orders';
  const RENDER_URL = 'https://coupang-dashboard.onrender.com/api/orders';
  const DASHBOARD_URL = 'https://coupang-dashboard.onrender.com/index.html';

  // 等待頁面完全載入
  function waitForLoad() {
    return new Promise(resolve => {
      if (document.readyState === 'complete') {
        setTimeout(resolve, 3000);
      } else {
        window.addEventListener('load', () => setTimeout(resolve, 3000));
      }
    });
  }

  // 提取訂單
  function extractOrders() {
    const orders = [];
    const cards = document.querySelectorAll('div.sc-fimazj-0');

    if (cards.length === 0) return orders;

    cards.forEach((card, idx) => {
      try {
        const text = card.innerText;

        const dateMatch = text.match(/(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\s*訂購/);
        const date = dateMatch
          ? dateMatch[1] + '-' + dateMatch[2].padStart(2, '0') + '-' + dateMatch[3].padStart(2, '0')
          : '';

        const statusMatch = text.match(/(配送中|已完成|配送完成|已送達|已取消|處理中|退貨|退款|準備中)/);
        const status = statusMatch ? statusMatch[1] : '';

        const products = card.querySelectorAll('div.sc-9cwg9-5');

        if (products.length > 0) {
          products.forEach((prod, pi) => {
            const pText = prod.innerText;
            const priceMatch = pText.match(/\$([\d,]+)/);
            const qtyMatch = pText.match(/(\d+)\s*件/);
            const lines = pText.split('\n').map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 3; });
            const name = lines.find(function(l) {
              return !l.match(/^\$/) && !l.match(/^\d+\s*件/) &&
                !l.match(/^(加入購物車|查看)/) && l.length > 5;
            }) || '';

            const link = prod.closest('a') || prod.querySelector('a');
            const img = prod.querySelector('img') || card.querySelectorAll('img')[pi];

            if (name || priceMatch) {
              orders.push({
                orderId: 'coupang-' + date + '-' + idx + '-' + pi,
                date: date,
                name: name,
                price: priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0,
                quantity: qtyMatch ? parseInt(qtyMatch[1]) : 1,
                status: status,
                productLink: link ? link.href : '',
                imageUrl: img ? img.src : ''
              });
            }
          });
        } else {
          var priceMatch = text.match(/\$([\d,]+)/);
          var qtyMatch = text.match(/(\d+)\s*件/);
          var lines = text.split('\n').map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 3; });
          var name = lines.find(function(l) {
            return !l.match(/^\d{4}\./) && !l.match(/^\$/) && !l.match(/^\d+\s*件/) &&
              !l.match(/^(配送|已完成|已送達|已取消|處理中|退貨|查看|加入|訂購|預計|今天)/) &&
              l.length > 5;
          }) || '';

          orders.push({
            orderId: 'coupang-' + date + '-' + idx,
            date: date,
            name: name,
            price: priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0,
            quantity: qtyMatch ? parseInt(qtyMatch[1]) : 1,
            status: status
          });
        }
      } catch (e) {
        console.warn('[Coupang 提取] 卡片 ' + idx + ' 失敗:', e);
      }
    });

    return orders;
  }

  // 傳送到 server（單一目標）
  function postOrders(url, orders) {
    return new Promise(function(resolve, reject) {
      GM_xmlhttpRequest({
        method: 'POST',
        url: url,
        headers: { 'Content-Type': 'application/json' },
        data: JSON.stringify(orders),
        onload: function(response) {
          try {
            var result = JSON.parse(response.responseText);
            resolve(result);
          } catch (e) {
            reject(new Error('Invalid response'));
          }
        },
        onerror: function(err) {
          reject(err);
        }
      });
    });
  }

  // 傳送到 server（本地優先，失敗則 fallback 到 Render）
  function sendToServer(orders) {
    return postOrders(SERVER_URL, orders).catch(function() {
      console.log('[Coupang 提取] 本地 Server 無回應，改傳 Render...');
      return postOrders(RENDER_URL, orders);
    });
  }

  // 顯示通知
  function showNotification(title, text) {
    var div = document.createElement('div');
    div.innerHTML =
      '<div style="position:fixed;top:20px;right:20px;z-index:99999;background:#1a1d28;color:#e4e4e7;' +
      'padding:16px 20px;border-radius:12px;border:1px solid #c33332;box-shadow:0 4px 20px rgba(0,0,0,0.5);' +
      'font-family:-apple-system,sans-serif;font-size:14px;max-width:350px">' +
      '<div style="font-weight:700;margin-bottom:4px;color:#e04444">' + title + '</div>' +
      '<div style="color:#9ca3af;font-size:13px">' + text + '</div>' +
      '<a href="' + DASHBOARD_URL + '" target="_blank" ' +
      'style="display:inline-block;margin-top:8px;color:#3b82f6;font-size:13px;text-decoration:none">' +
      '開啟儀表板 →</a></div>';
    document.body.appendChild(div);
    setTimeout(function() { div.remove(); }, 8000);
  }

  // 主流程
  function main() {
    waitForLoad().then(function() {
      var orders = extractOrders();
      console.log('[Coupang 提取] 找到 ' + orders.length + ' 筆訂單');

      if (orders.length === 0) {
        console.log('[Coupang 提取] 未找到訂單，可能頁面結構已變更');
        return;
      }

      sendToServer(orders).then(function(result) {
        console.log('[Coupang 提取] Server 回應:', result);
        showNotification(
          '已同步 ' + result.added + ' 筆新訂單',
          '共 ' + result.total + ' 筆訂單已儲存'
        );
      }).catch(function(err) {
        console.warn('[Coupang 提取] 無法連線到 Server:', err);
        showNotification(
          '無法連線到分析 Server',
          '請確認 server 已啟動：node coupang/server.mjs'
        );
      });
    });
  }

  main();
})();
