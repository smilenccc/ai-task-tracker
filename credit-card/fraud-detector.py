#!/usr/bin/env python3
"""
信用卡盜刷偵測系統
分析消費記錄，找出可疑交易
"""

import json
import statistics
from datetime import datetime
from typing import List, Dict, Tuple

class FraudDetector:
    def __init__(self, transactions_file: str, whitelist_file: str = 'whitelist.json'):
        with open(transactions_file, 'r', encoding='utf-8') as f:
            self.transactions = json.load(f)
        
        # 載入白名單
        try:
            with open(whitelist_file, 'r', encoding='utf-8') as f:
                self.whitelist = json.load(f)
        except FileNotFoundError:
            self.whitelist = {'allowed_duplicates': [], 'allowed_merchants': []}
        
        self.suspicious = []
        self.alerts = []
    
    def analyze(self) -> Dict:
        """執行完整分析"""
        self._check_duplicate_merchants()  # 優先檢查！
        self._check_high_amount()
        self._check_suspicious_merchants()
        self._check_unusual_time()
        # self._check_foreign_transactions()  # 誤報太多，暫時停用
        self._check_rapid_transactions()
        self._check_unusual_category()
        
        return {
            'total_transactions': len(self.transactions),
            'suspicious_count': len(self.suspicious),
            'suspicious_transactions': self.suspicious,
            'alerts': self.alerts,
            'risk_level': self._calculate_risk()
        }
    
    def _check_duplicate_merchants(self):
        """檢查同一商家重複刷卡"""
        merchant_counts = {}
        merchant_transactions = {}
        
        for t in self.transactions:
            # 移除分期資訊來辨識基礎商家
            merchant = t['description']
            
            # 移除分期標記
            for pattern in ['分01期之第01期', '分02期之第01期', '分03期之第01期',
                          '分01期之第02期', '分02期之第02期', '分03期之第02期',
                          '分03期之第03期']:
                merchant = merchant.replace(pattern, '').strip()
            
            # 移除後面的日期/編號
            merchant = merchant.split('　')[0].strip()
            
            # 計數
            if merchant not in merchant_counts:
                merchant_counts[merchant] = 0
                merchant_transactions[merchant] = []
            
            merchant_counts[merchant] += 1
            merchant_transactions[merchant].append(t)
        
        # 找出重複刷卡（排除已知的分期付款和白名單）
        for merchant, count in merchant_counts.items():
            if count >= 2:
                trans_list = merchant_transactions[merchant]
                
                # 檢查是否為分期付款
                is_installment = any('分' in t['description'] and '期' in t['description'] 
                                    for t in trans_list)
                
                # 檢查是否在白名單中
                is_whitelisted = any(allowed in merchant for allowed in self.whitelist.get('allowed_duplicates', []))
                
                # 檢查是否同一天多次（更可疑）
                dates = [t['date'] for t in trans_list]
                same_day_duplicates = len(dates) != len(set(dates))
                
                # 如果不是分期且不在白名單，或是同一天多次刷卡
                if not is_installment:
                    if same_day_duplicates and not is_whitelisted:
                        # 同一天重複刷卡，高度可疑！
                        for t in trans_list:
                            if t not in self.suspicious:
                                self.suspicious.append(t)
                        
                        self.alerts.append({
                            'type': '同日重複刷卡',
                            'severity': 'critical',
                            'merchant': merchant,
                            'count': count,
                            'transactions': trans_list,
                            'reason': f"🚨 同一天在「{merchant}」刷了多次（高度可疑！）"
                        })
                    elif not is_whitelisted and count >= 3:
                        # 非白名單且刷3次以上，中度可疑
                        for t in trans_list:
                            if t not in self.suspicious:
                                self.suspicious.append(t)
                        
                        self.alerts.append({
                            'type': '重複刷卡',
                            'severity': 'medium',
                            'merchant': merchant,
                            'count': count,
                            'transactions': trans_list,
                            'reason': f"同一商家「{merchant}」刷了 {count} 次（請確認是否正常）"
                        })
    
    def _check_high_amount(self):
        """檢查異常高額消費"""
        amounts = [t['amount'] for t in self.transactions]
        if not amounts:
            return
        
        avg = statistics.mean(amounts)
        std = statistics.stdev(amounts) if len(amounts) > 1 else 0
        threshold = avg + (2 * std)  # 超過平均 + 2 個標準差
        
        for t in self.transactions:
            if t['amount'] > threshold and t['amount'] > avg * 3:
                self.suspicious.append(t)
                self.alerts.append({
                    'type': '異常高額',
                    'severity': 'high',
                    'transaction': t,
                    'reason': f"金額 ${t['amount']:,} 遠超過平均 ${avg:,.0f}"
                })
    
    def _check_suspicious_merchants(self):
        """檢查可疑商家"""
        suspicious_keywords = [
            '博弈', '賭場', 'CASINO', 'BET', '成人', 'ADULT',
            '虛擬貨幣', 'CRYPTO', 'BITCOIN', '不明', 'UNKNOWN'
        ]
        
        for t in self.transactions:
            desc = t['description'].upper()
            for keyword in suspicious_keywords:
                if keyword.upper() in desc:
                    if t not in self.suspicious:
                        self.suspicious.append(t)
                    self.alerts.append({
                        'type': '可疑商家',
                        'severity': 'critical',
                        'transaction': t,
                        'reason': f"商家名稱包含可疑關鍵字：{keyword}"
                    })
                    break
    
    def _check_unusual_time(self):
        """檢查異常時間（需要時間資訊）"""
        # 目前資料沒有時間，僅檢查日期
        pass
    
    def _check_foreign_transactions(self):
        """檢查國外交易"""
        foreign_keywords = [
            'PAYPAL', 'AMAZON.COM', 'GOOGLE', 'APPLE.COM', 
            'NETFLIX', 'SPOTIFY', 'YOUTUBE'
        ]
        
        common_foreign = ['PAYPAL', 'GOOGLE', 'APPLE', 'YOUTUBE']  # 常見的不算異常
        
        for t in self.transactions:
            desc = t['description'].upper()
            
            # 檢查是否為國外交易（簡化：檢查英文商家名）
            if any(c.isalpha() and c.isupper() for c in desc):
                # 排除常見的合法國外服務
                is_common = any(common in desc for common in common_foreign)
                
                if not is_common and not any(keyword in desc for keyword in ['康是美', '肉圓', '運通', '特斯拉', 'ETAG']):
                    self.alerts.append({
                        'type': '國外交易',
                        'severity': 'medium',
                        'transaction': t,
                        'reason': f"可能為國外交易：{t['description']}"
                    })
    
    def _check_rapid_transactions(self):
        """檢查短時間多筆交易"""
        # 按日期分組
        by_date = {}
        for t in self.transactions:
            date = t['date']
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(t)
        
        # 檢查單日超過 5 筆
        for date, trans in by_date.items():
            if len(trans) >= 5:
                self.alerts.append({
                    'type': '短時間多筆',
                    'severity': 'medium',
                    'date': date,
                    'count': len(trans),
                    'reason': f"{date} 當天有 {len(trans)} 筆交易（可能異常）"
                })
    
    def _check_unusual_category(self):
        """檢查不尋常的消費類別"""
        # 建立消費習慣模型（簡化版）
        categories = {}
        for t in self.transactions:
            cat = self._categorize(t['description'])
            categories[cat] = categories.get(cat, 0) + 1
        
        # 找出只出現 1 次的罕見類別
        rare_categories = [cat for cat, count in categories.items() if count == 1]
        
        for t in self.transactions:
            cat = self._categorize(t['description'])
            if cat in rare_categories and t['amount'] > 1000:
                self.alerts.append({
                    'type': '不尋常消費',
                    'severity': 'low',
                    'transaction': t,
                    'reason': f"罕見消費類別：{cat}"
                })
    
    def _categorize(self, description: str) -> str:
        """簡易分類"""
        desc = description.upper()
        
        if any(kw in desc for kw in ['肉圓', '豆花', '餐', '食', '飯']):
            return '餐飲'
        elif any(kw in desc for kw in ['ETAG', '運通', '特斯拉', '停車']):
            return '交通'
        elif any(kw in desc for kw in ['康是美', 'COUPANG', '購物']):
            return '購物'
        elif any(kw in desc for kw in ['YOUTUBE', 'APPLE', 'NETFLIX', '海洋館']):
            return '娛樂'
        elif any(kw in desc for kw in ['中華電信', '會員', '訂閱']):
            return '訂閱'
        else:
            return '其他'
    
    def _calculate_risk(self) -> str:
        """計算風險等級"""
        critical = sum(1 for a in self.alerts if a.get('severity') == 'critical')
        high = sum(1 for a in self.alerts if a.get('severity') == 'high')
        medium = sum(1 for a in self.alerts if a.get('severity') == 'medium')
        
        if critical > 0:
            return 'CRITICAL'
        elif high > 2:
            return 'HIGH'
        elif high > 0 or medium > 3:
            return 'MEDIUM'
        elif medium > 0:
            return 'LOW'
        else:
            return 'SAFE'
    
    def generate_report(self) -> str:
        """生成報告"""
        result = self.analyze()
        
        report = f"""
🔍 信用卡盜刷偵測報告
{'=' * 50}

📊 統計資訊：
  - 總交易筆數：{result['total_transactions']}
  - 可疑交易：{result['suspicious_count']}
  - 風險等級：{result['risk_level']}

"""
        
        if result['alerts']:
            report += f"\n⚠️ 警示清單（共 {len(result['alerts'])} 項）：\n"
            report += "=" * 50 + "\n\n"
            
            for i, alert in enumerate(result['alerts'], 1):
                severity_icon = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '⚡',
                    'low': 'ℹ️'
                }.get(alert.get('severity'), '📌')
                
                report += f"{severity_icon} 警示 #{i}：{alert['type']}\n"
                report += f"   原因：{alert['reason']}\n"
                
                # 特殊處理重複刷卡
                if alert['type'] == '重複刷卡' and 'transactions' in alert:
                    report += f"   商家：{alert['merchant']}\n"
                    report += f"   刷卡次數：{alert['count']} 次\n"
                    report += f"   明細：\n"
                    for t in alert['transactions']:
                        report += f"     - {t['date']}: ${t['amount']:,}\n"
                elif 'transaction' in alert:
                    t = alert['transaction']
                    report += f"   日期：{t['date']}\n"
                    report += f"   商家：{t['description']}\n"
                    report += f"   金額：${t['amount']:,}\n"
                
                report += "\n"
        else:
            report += "\n✅ 未發現可疑交易，帳單正常！\n"
        
        return report


if __name__ == '__main__':
    detector = FraudDetector('transactions.json')
    print(detector.generate_report())
