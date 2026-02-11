// ==UserScript==
// @name         Coupang 訂單自動提取 (VPS版)
// @namespace    https://github.com/smilenccc/ai-task-tracker
// @version      1.3
// @description  自動提取 Coupang 訂單資料並傳送到 VPS 分析 Server
// @author       小八 + 小Linda
// @match        https://mc.tw.coupang.com/ssr/desktop/order/*
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @connect      157.180.126.133
// @connect      coupang-dashboard.onrender.com
// ==/UserScript==

(function() {
    'use strict';

    // VPS Server 優先，Render 備援
    var SERVER_URL = 'http://157.180.126.133:5566/api/orders';
    var RENDER_URL = 'https://coupang-dashboard.onrender.com/api/orders';
    var DASHBOARD_URL = 'https://coupang-dashboard.onrender.com/index.html';

    var lastUrl = location.href;
    var isRunning = false;

    function extractOrders() {
        var orders = [];
        var cards = document.querySelectorAll('div.sc-fimazj-0');
        if (cards.length === 0) return orders;

        cards.forEach(function(card, idx) {
            try {
                var text = card.innerText;
                var dateMatch = text.match(/(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\s*訂購/);
                var date = dateMatch ? dateMatch[1] + '-' + dateMatch[2].padStart(2, '0') + '-' + dateMatch[3].padStart(2, '0') : '';
                
                var statusMatch = text.match(/(配送中|已完成|配送完成|已送達|已取消|處理中|退貨|退款|準備中)/);
                var status = statusMatch ? statusMatch[1] : '';

                var products = card.querySelectorAll('div.sc-9cwg9-5');
                
                if (products.length > 0) {
                    products.forEach(function(prod, pi) {
                        var pText = prod.innerText;
                        var priceMatch = pText.match(/\$([\d,]+)/);
                        var qtyMatch = pText.match(/(\d+)\s*件/);
                        
                        var lines = pText.split('\n').map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 3; });
                        var name = lines.find(function(l) {
                            return !l.match(/^\$/) && !l.match(/^\d+\s*件/) && !l.match(/^(加入購物車|查看)/) && l.length > 5;
                        }) || '';

                        var link = prod.closest('a') || prod.querySelector('a');
                        var img = prod.querySelector('img') || card.querySelectorAll('img')[pi];

                        if (name && priceMatch) {
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
                               !l.match(/^(配送|已完成|已送達|已取消|處理中|退貨|查看|加入|訂購|預計|今天)/) && l.length > 5;
                    }) || '';

                    if (name && priceMatch) {
                        orders.push({
                            orderId: 'coupang-' + date + '-' + idx,
                            date: date,
                            name: name,
                            price: priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0,
                            quantity: qtyMatch ? parseInt(qtyMatch[1]) : 1,
                            status: status
                        });
                    }
                }
            } catch (e) {
                console.warn('[Coupang 提取] 卡片 ' + idx + ' 失敗:', e);
            }
        });

        return orders;
    }

    function postOrders(url, orders) {
        return new Promise(function(resolve, reject) {
            GM_xmlhttpRequest({
                method: 'POST',
                url: url,
                headers: { 'Content-Type': 'application/json' },
                data: JSON.stringify(orders),
                timeout: 10000,
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
                },
                ontimeout: function() {
                    reject(new Error('Timeout'));
                }
            });
        });
    }

    function sendToServer(orders) {
        console.log('[Coupang 提取] 嘗試連接 VPS Server...');
        return postOrders(SERVER_URL, orders).catch(function(err) {
            console.log('[Coupang 提取] VPS 無回應:', err.message);
            console.log('[Coupang 提取] 改傳 Render 備援...');
            return postOrders(RENDER_URL, orders);
        });
    }

    function showNotification(title, text, color) {
        var old = document.getElementById('coupang-notify');
        if (old) old.remove();

        var div = document.createElement('div');
        div.id = 'coupang-notify';
        div.innerHTML = '<div style="position:fixed;top:20px;right:20px;z-index:99999;background:#1a1d28;color:#e4e4e7;' +
            'padding:16px 20px;border-radius:12px;border:1px solid ' + (color || '#c33332') + ';box-shadow:0 4px 20px rgba(0,0,0,0.5);' +
            'font-family:-apple-system,sans-serif;font-size:14px;max-width:350px">' +
            '<div style="font-weight:700;margin-bottom:4px;color:#e04444">' + title + '</div>' +
            '<div style="color:#9ca3af;font-size:13px">' + text + '</div>' +
            '<a href="' + DASHBOARD_URL + '" target="_blank" ' +
            'style="display:inline-block;margin-top:8px;color:#3b82f6;font-size:13px;text-decoration:none">' +
            '開啟儀表板 →</a></div>';
        
        document.body.appendChild(div);
        setTimeout(function() { div.remove(); }, 8000);
    }

    function updateButton(text, color) {
        var btn = document.getElementById('coupang-grab-btn');
        if (btn) {
            btn.textContent = text;
            btn.style.background = color || '#c33332';
        }
    }

    function grabCurrentPage() {
        if (isRunning) return;
        isRunning = true;
        updateButton('抓取中...', '#666');

        setTimeout(function() {
            var orders = extractOrders();
            console.log('[Coupang 提取] 找到 ' + orders.length + ' 筆訂單');

            if (orders.length === 0) {
                updateButton('未找到訂單', '#f59e0b');
                showNotification('未找到訂單', '請確認頁面已完全載入', '#f59e0b');
                setTimeout(function() {
                    updateButton('抓取訂單', '#c33332');
                }, 2000);
                isRunning = false;
                return;
            }

            sendToServer(orders).then(function(result) {
                console.log('[Coupang 提取] Server 回應:', result);
                showNotification(
                    '✅ 已同步 ' + result.added + ' 筆新訂單',
                    '共 ' + result.total + ' 筆訂單已儲存並推送到 GitHub',
                    '#22c55e'
                );
                updateButton('完成 +' + result.added, '#22c55e');
                setTimeout(function() {
                    updateButton('抓取訂單', '#c33332');
                }, 3000);
                isRunning = false;
            }).catch(function(err) {
                console.warn('[Coupang 提取] 無法連線到任何 Server:', err);
                showNotification(
                    '❌ 無法連線到分析 Server',
                    'VPS 和 Render 都無回應，請檢查網路',
                    '#ef4444'
                );
                updateButton('連線失敗', '#ef4444');
                setTimeout(function() {
                    updateButton('抓取訂單', '#c33332');
                }, 3000);
                isRunning = false;
            });
        }, 1000);
    }

    // 建立浮動按鈕
    function createButton() {
        var btn = document.createElement('button');
        btn.id = 'coupang-grab-btn';
        btn.textContent = '抓取訂單';
        btn.style.cssText = 'position:fixed;bottom:30px;right:30px;z-index:99999;' +
            'background:#c33332;color:#fff;border:none;border-radius:12px;' +
            'padding:12px 20px;font-size:15px;font-weight:700;cursor:pointer;' +
            'box-shadow:0 4px 15px rgba(195,51,50,0.4);' +
            'font-family:-apple-system,sans-serif;transition:all 0.3s;';
        
        btn.addEventListener('mouseenter', function() {
            btn.style.transform = 'translateY(-2px)';
            btn.style.boxShadow = '0 6px 20px rgba(195,51,50,0.5)';
        });
        
        btn.addEventListener('mouseleave', function() {
            btn.style.transform = 'translateY(0)';
            btn.style.boxShadow = '0 4px 15px rgba(195,51,50,0.4)';
        });
        
        btn.addEventListener('click', grabCurrentPage);
        document.body.appendChild(btn);
    }

    // 監聽 URL 變化（SPA 換頁偵測）
    function watchUrlChange() {
        setInterval(function() {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                console.log('[Coupang 提取] 偵測到換頁，3 秒後自動抓取...');
                updateButton('換頁偵測中...', '#3b82f6');
                setTimeout(function() {
                    grabCurrentPage();
                }, 3000);
            }
        }, 1000);
    }

    // 啟動
    function init() {
        createButton();
        watchUrlChange();
        // 首次載入也自動抓
        setTimeout(grabCurrentPage, 3000);
    }

    if (document.readyState === 'complete') {
        init();
    } else {
        window.addEventListener('load', init);
    }
})();
