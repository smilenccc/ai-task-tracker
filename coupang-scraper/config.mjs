// Coupang 酷澎台灣 — 爬蟲設定常數

export const URLS = {
  base: 'https://www.tw.coupang.com',
  // 登入 URL（多種可能格式，爬蟲會嘗試 + 從首頁動態發現）
  loginCandidates: [
    'https://login.tw.coupang.com/',
    'https://www.tw.coupang.com/login',
    'https://member.tw.coupang.com/login',
    'https://member.tw.coupang.com/account/login',
  ],
  // 訂單頁 URL（從首頁發現的真正 URL 在第一個）
  orderHistoryCandidates: [
    'https://mc.tw.coupang.com/ssr/desktop/order/list',
    'https://www.tw.coupang.com/buyer/order-history',
    'https://www.tw.coupang.com/order/list',
  ],
};

// DOM 選擇器（首次 headed 模式執行後可能需要調整）
export const SELECTORS = {
  // 首頁登入連結（從首頁找到登入按鈕）
  homeLogin: 'a[href*="login"], a[href*="signin"], [class*="login"], [class*="sign-in"], button:has-text("登入"), a:has-text("登入"), a:has-text("Login")',

  // 登入頁
  login: {
    emailInput: 'input[name="email"], input[type="email"], #login-email-input, input[name="username"], input[placeholder*="email"], input[placeholder*="信箱"], input[placeholder*="帳號"]',
    passwordInput: 'input[name="password"], input[type="password"], #login-password-input, input[placeholder*="密碼"], input[placeholder*="password"]',
    submitButton: 'button[type="submit"], .login-btn, .login__button, button:has-text("登入"), button:has-text("Login"), input[type="submit"]',
    loginSuccess: '.my-coupang, .user-info, [class*="mypage"], [class*="order"]',
  },

  // 訂單歷史頁
  orders: {
    // 訂單容器（各種可能的 class 名稱）
    orderItem: '[class*="order-item"], [class*="order-list"] > div, [class*="orderList"] > li, .order-card',
    // 訂單內欄位
    orderId: '[class*="order-id"], [class*="orderId"], [class*="order-number"]',
    orderDate: '[class*="order-date"], [class*="orderDate"], time',
    productName: '[class*="product-name"], [class*="productName"], [class*="item-name"]',
    productPrice: '[class*="price"], [class*="total-price"], [class*="amount"]',
    productImage: '[class*="product"] img, [class*="item"] img',
    productLink: '[class*="product"] a, [class*="item-name"] a',
    quantity: '[class*="quantity"], [class*="qty"], [class*="count"]',
    orderStatus: '[class*="status"], [class*="delivery"], [class*="shipping"]',
    // 分頁
    nextPage: '[class*="next"], [class*="pagination"] a:last-child, button[aria-label="next"]',
    pageNumbers: '[class*="pagination"] a, [class*="pagination"] button',
  },
};

// 爬蟲行為設定
export const SCRAPER_CONFIG = {
  // Playwright 啟動選項
  browser: {
    slowMo: 100,
    // 首次使用 headed 模式觀察頁面結構
    headless: process.env.HEADED !== '1' ? true : false,
  },

  // 反爬蟲
  userAgent:
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',

  // 延遲設定（毫秒）
  delay: {
    min: 800,
    max: 2500,
    afterLogin: 4000,
    betweenPages: 2000,
  },

  // Session 持久化
  authStatePath: '.auth/coupang-session.json',

  // 資料輸出
  outputPath: '../purchases.json',

  // 最大爬取頁數（防止無限迴圈）
  maxPages: 50,

  // 訂單歷史往回追溯的月份數（0 = 全部）
  monthsBack: 0,
};

// 商品自動分類規則
export const CATEGORIES = {
  '食品/飲料': [
    '咖啡', '茶', '水', '飲料', '零食', '餅乾', '巧克力', '糖果',
    '米', '麵', '醬', '油', '鹽', '糖', '醋', '食品', '堅果',
    '牛奶', '優格', '果汁', '啤酒', '酒', '泡麵', '罐頭', '調味',
    '雞', '豬', '牛', '魚', '蝦', '肉', '蔬菜', '水果',
    '麵包', '蛋糕', '冰淇淋', '起司', '奶油',
  ],
  '3C/電子': [
    '手機', '耳機', '充電', '電池', '線材', 'USB', 'HDMI',
    '鍵盤', '滑鼠', 'iPad', 'iPhone', 'Samsung', '平板',
    '記憶卡', 'SD', 'SSD', '硬碟', '螢幕', '音響', '喇叭',
    'AirPods', 'Apple', '電腦', '筆電', 'Switch', 'PS5',
    '相機', '鏡頭', 'GoPro', '投影', '路由器', 'WiFi',
  ],
  '日用品/清潔': [
    '衛生紙', '面紙', '洗衣', '洗碗', '清潔', '垃圾袋',
    '牙刷', '牙膏', '洗髮', '沐浴', '肥皂', '洗手',
    '拖把', '掃把', '刷子', '海綿', '漂白', '除臭',
    '柔軟', '芳香', '殺菌', '消毒',
  ],
  '美妝/保養': [
    '面膜', '化妝', '口紅', '眼影', '粉底', '防曬',
    '乳液', '精華', '卸妝', '保濕', '面霜', '護手',
    '香水', '指甲', '眉筆', '睫毛', '腮紅',
  ],
  '服飾/配件': [
    '衣', '褲', '裙', '外套', '帽', '襪', '鞋',
    '包包', '背包', '皮夾', '手錶', '項鍊', '耳環',
    '圍巾', '手套', '皮帶', '太陽眼鏡',
  ],
  '居家/傢俱': [
    '枕頭', '棉被', '床單', '毛巾', '窗簾', '地毯',
    '收納', '置物', '掛鉤', '燈', '蠟燭', '花瓶',
    '碗', '盤', '杯', '筷', '鍋', '刀', '砧板',
  ],
  '健康/運動': [
    '維他命', '保健', '營養', '蛋白', '益生菌',
    '口罩', 'OK繃', '體溫', '血壓',
    '瑜珈', '啞鈴', '跑步', '運動', '健身',
  ],
  '母嬰/寵物': [
    '尿布', '奶瓶', '奶嘴', '嬰兒', '寶寶',
    '貓', '狗', '飼料', '貓砂', '寵物',
  ],
  '書籍/文具': [
    '書', '筆', '筆記本', '文具', '膠帶', '剪刀',
    '便利貼', '資料夾', '計算機',
  ],
};

// 根據商品名稱自動分類
export function categorize(productName) {
  const name = productName.toLowerCase();
  for (const [category, keywords] of Object.entries(CATEGORIES)) {
    if (keywords.some((kw) => name.includes(kw.toLowerCase()))) {
      return category;
    }
  }
  return '其他';
}
