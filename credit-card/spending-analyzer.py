#!/usr/bin/env python3
"""
消費習慣分析系統
分析消費平台、地點頻率、購買品項，並做跨月比較
"""

import json
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple

class SpendingAnalyzer:
    def __init__(self, transactions_file: str):
        with open(transactions_file, 'r', encoding='utf-8') as f:
            self.transactions = json.load(f)
        
        self.platforms = defaultdict(lambda: {'count': 0, 'total': 0, 'items': []})
        self.categories = defaultdict(lambda: {'count': 0, 'total': 0, 'items': []})
        self.monthly_data = defaultdict(lambda: defaultdict(list))
    
    def analyze(self) -> Dict:
        """執行完整分析"""
        # 基礎統計
        platform_stats = self._analyze_platforms()
        category_stats = self._analyze_categories()
        monthly_comparison = self._compare_months()
        repeat_purchases = self._find_repeat_purchases()
        location_frequency = self._analyze_locations()
        
        return {
            'platforms': platform_stats,
            'categories': category_stats,
            'monthly_comparison': monthly_comparison,
            'repeat_purchases': repeat_purchases,
            'locations': location_frequency,
            'total_transactions': len(self.transactions)
        }
    
    def _extract_platform(self, description: str) -> str:
        """提取消費平台"""
        desc = description.upper()
        
        # 線上平台
        if 'COUPANG' in desc or 'ＣＯＵＰＡＮＧ' in desc:
            return 'Coupang 酷澎'
        elif 'PCHOME' in desc or 'ＰＣＨＯＭＥ' in desc:
            return 'PChome 24h購物'
        elif '康是美' in desc:
            return '康是美（91APP）'
        elif 'YOUTUBE' in desc:
            return 'YouTube Premium'
        elif 'APPLE' in desc:
            return 'Apple 服務'
        elif 'GOOGLE' in desc:
            return 'Google 服務'
        elif 'SPOTIFY' in desc:
            return 'Spotify'
        elif 'RENDER.COM' in desc:
            return 'Render.com'
        elif '樂天' in desc:
            return '樂天市場'
        
        # 實體店家
        elif '肉圓' in desc:
            return '肉圓李（大里店）'
        elif '豆花' in desc:
            return '統元豆花'
        elif '達美樂' in desc:
            return '達美樂披薩'
        elif 'COCO' in desc or 'ｃｏｃｏ' in desc:
            return 'CoCo都可'
        elif '海洋館' in desc:
            return 'Xpark 水族館'
        
        # 交通/服務
        elif 'ETAG' in desc or 'ｅＴａｇ' in desc:
            return 'eTag 高速公路'
        elif '運通' in desc:
            return '阜爾運通（悠遊卡）'
        elif '中華電信' in desc:
            return '中華電信'
        elif '酷澎ＷＯＷ' in desc:
            return 'Coupang WOW會員'
        elif '特斯拉' in desc:
            return 'Tesla'
        
        else:
            # 移除編號和日期後的商家名稱
            clean = description.split('　')[0].strip()
            return clean[:20]  # 限制長度
    
    def _extract_item(self, description: str) -> str:
        """提取商品品項（簡化版）"""
        desc = description
        
        # 食品
        if '肉圓' in desc:
            return '肉圓'
        elif '豆花' in desc:
            return '豆花'
        elif '披薩' in desc or '達美樂' in desc:
            return '披薩'
        elif '飲料' in desc or 'COCO' in desc or 'ｃｏｃｏ' in desc:
            return '飲料'
        
        # 服務
        elif 'YOUTUBE' in desc.upper():
            return 'YouTube Premium 訂閱'
        elif 'SPOTIFY' in desc.upper():
            return 'Spotify 訂閱'
        elif 'ETAG' in desc.upper() or 'ｅＴａｇ' in desc:
            return 'eTag 儲值'
        elif '運通' in desc:
            return '悠遊卡加值'
        elif '中華電信' in desc:
            return '手機費'
        elif '酷澎ＷＯＷ' in desc:
            return 'Coupang WOW 會員費'
        elif 'RENDER' in desc.upper():
            return 'Render 雲端服務'
        elif '海洋館' in desc:
            return '水族館門票'
        
        # 網購
        elif 'COUPANG' in desc.upper() or 'ＣＯＵＰＡＮＧ' in desc:
            return 'Coupang 網購'
        elif 'PCHOME' in desc.upper() or 'ＰＣＨＯＭＥ' in desc:
            return 'PChome 網購'
        elif '康是美' in desc:
            if '分期' in desc:
                return '康是美網購（分期）'
            return '康是美網購'
        
        return '其他'
    
    def _get_month(self, date_str: str) -> str:
        """提取年月"""
        try:
            # 格式：2025/12/10
            year, month, _ = date_str.split('/')
            return f"{year}/{month}"
        except:
            return '未知'
    
    def _analyze_platforms(self) -> List[Dict]:
        """分析消費平台"""
        for t in self.transactions:
            platform = self._extract_platform(t['description'])
            self.platforms[platform]['count'] += 1
            self.platforms[platform]['total'] += t['amount']
            self.platforms[platform]['items'].append(t)
        
        # 排序（依次數）
        sorted_platforms = sorted(
            self.platforms.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return [
            {
                'name': name,
                'count': data['count'],
                'total_amount': data['total'],
                'avg_amount': data['total'] // data['count']
            }
            for name, data in sorted_platforms
        ]
    
    def _analyze_categories(self) -> List[Dict]:
        """分析消費類別"""
        for t in self.transactions:
            category = self._categorize(t['description'])
            item = self._extract_item(t['description'])
            
            self.categories[category]['count'] += 1
            self.categories[category]['total'] += t['amount']
            self.categories[category]['items'].append(item)
        
        sorted_categories = sorted(
            self.categories.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )
        
        result = []
        for cat, data in sorted_categories:
            # 統計品項
            item_counter = Counter(data['items'])
            top_items = item_counter.most_common(3)
            
            result.append({
                'category': cat,
                'count': data['count'],
                'total_amount': data['total'],
                'top_items': [{'item': item, 'count': count} for item, count in top_items]
            })
        
        return result
    
    def _compare_months(self) -> Dict:
        """跨月比較"""
        # 按月份分組
        for t in self.transactions:
            month = self._get_month(t['date'])
            item = self._extract_item(t['description'])
            platform = self._extract_platform(t['description'])
            
            self.monthly_data[month]['items'].append(item)
            self.monthly_data[month]['platforms'].append(platform)
            self.monthly_data[month]['transactions'].append(t)
        
        # 分析每個月
        monthly_summary = {}
        for month, data in sorted(self.monthly_data.items()):
            item_counter = Counter(data['items'])
            platform_counter = Counter(data['platforms'])
            total_amount = sum(t['amount'] for t in data['transactions'])
            
            monthly_summary[month] = {
                'total_amount': total_amount,
                'transaction_count': len(data['transactions']),
                'top_items': item_counter.most_common(5),
                'top_platforms': platform_counter.most_common(5)
            }
        
        return monthly_summary
    
    def _find_repeat_purchases(self) -> List[Dict]:
        """找出重複購買的品項"""
        all_items = []
        for t in self.transactions:
            item = self._extract_item(t['description'])
            month = self._get_month(t['date'])
            all_items.append((item, month, t))
        
        # 統計品項出現次數
        item_months = defaultdict(set)
        item_transactions = defaultdict(list)
        
        for item, month, trans in all_items:
            if item != '其他':
                item_months[item].add(month)
                item_transactions[item].append((month, trans))
        
        # 找出跨月購買的品項
        repeats = []
        for item, months in item_months.items():
            if len(months) >= 2:
                transactions = item_transactions[item]
                repeats.append({
                    'item': item,
                    'months': sorted(list(months)),
                    'total_purchases': len(transactions),
                    'details': [
                        {
                            'month': month,
                            'amount': trans['amount'],
                            'description': trans['description']
                        }
                        for month, trans in transactions
                    ]
                })
        
        return sorted(repeats, key=lambda x: x['total_purchases'], reverse=True)
    
    def _analyze_locations(self) -> List[Dict]:
        """分析消費地點頻率"""
        locations = defaultdict(lambda: {'count': 0, 'total': 0})
        
        for t in self.transactions:
            desc = t['description']
            location = '線上'
            
            # 判斷實體/線上
            if any(kw in desc for kw in ['COUPANG', 'ＣＯＵＰＡＮＧ', 'PCHOME', 'ＰＣＨＯＭＥ', 
                                          'YOUTUBE', 'SPOTIFY', 'APPLE', 'GOOGLE', 
                                          '康是美', '樂天', 'RENDER']):
                location = '線上'
            elif '大里' in desc:
                location = '大里區'
            elif '北' in desc and ('台北' in desc or '捷運' in desc):
                location = '台北'
            elif 'ｅＴａｇ' in desc or 'ETAG' in desc:
                location = '高速公路'
            else:
                location = '實體店面'
            
            locations[location]['count'] += 1
            locations[location]['total'] += t['amount']
        
        return sorted(
            [
                {
                    'location': loc,
                    'count': data['count'],
                    'total_amount': data['total']
                }
                for loc, data in locations.items()
            ],
            key=lambda x: x['count'],
            reverse=True
        )
    
    def _categorize(self, description: str) -> str:
        """分類（與 fraud-detector 相同）"""
        desc = description.upper()
        
        if any(kw in desc for kw in ['肉圓', '豆花', '餐', '食', '飯', '披薩', 'COCO']):
            return '餐飲'
        elif any(kw in desc for kw in ['ETAG', '運通', '特斯拉', '停車']):
            return '交通'
        elif any(kw in desc for kw in ['康是美', 'COUPANG', 'PCHOME', '購物', '樂天']):
            return '購物'
        elif any(kw in desc for kw in ['YOUTUBE', 'APPLE', 'NETFLIX', '海洋館', 'SPOTIFY']):
            return '娛樂'
        elif any(kw in desc for kw in ['中華電信', '會員', '訂閱', 'RENDER', '酷澎ＷＯＷ']):
            return '訂閱'
        else:
            return '其他'
    
    def generate_report(self) -> str:
        """生成完整報告"""
        result = self.analyze()
        
        report = f"""
📊 消費習慣分析報告
{'=' * 60}

總交易筆數：{result['total_transactions']}

"""
        
        # 平台分析
        report += "\n🏪 消費平台統計（依次數排序）\n"
        report += "=" * 60 + "\n"
        for i, p in enumerate(result['platforms'][:10], 1):
            report += f"{i:2d}. {p['name']:<30} {p['count']:2d}次  NT${p['total_amount']:,}  (平均${p['avg_amount']:,}/次)\n"
        
        # 類別分析
        report += f"\n\n📦 消費類別統計（依金額排序）\n"
        report += "=" * 60 + "\n"
        for i, c in enumerate(result['categories'], 1):
            report += f"{i}. {c['category']:<15} {c['count']:2d}次  NT${c['total_amount']:,}\n"
            top_items_str = ', '.join([f"{item['item']}({item['count']}次)" for item in c['top_items']])
            report += f"   常買品項：{top_items_str}\n"
        
        # 地點分析
        report += f"\n\n📍 消費地點分析\n"
        report += "=" * 60 + "\n"
        for loc in result['locations']:
            report += f"• {loc['location']:<15} {loc['count']:2d}次  NT${loc['total_amount']:,}\n"
        
        # 月份比較
        report += f"\n\n📅 月份比較分析\n"
        report += "=" * 60 + "\n"
        for month, data in sorted(result['monthly_comparison'].items()):
            report += f"\n【{month}】\n"
            report += f"  消費金額：NT${data['total_amount']:,} ({data['transaction_count']}筆)\n"
            items_str = ', '.join([f"{item}({count}次)" for item, count in data['top_items'][:3]])
            platforms_str = ', '.join([f"{plat}({count}次)" for plat, count in data['top_platforms'][:3]])
            report += f"  常買品項：{items_str}\n"
            report += f"  常用平台：{platforms_str}\n"
        
        # 重複購買分析
        if result['repeat_purchases']:
            report += f"\n\n🔄 重複購買分析（跨月比較）\n"
            report += "=" * 60 + "\n"
            for rp in result['repeat_purchases'][:10]:
                report += f"\n✓ {rp['item']}\n"
                report += f"  購買月份：{', '.join(rp['months'])} (共{rp['total_purchases']}次)\n"
                for detail in rp['details']:
                    report += f"    • {detail['month']}: ${detail['amount']:,}\n"
        
        return report


if __name__ == '__main__':
    analyzer = SpendingAnalyzer('transactions.json')
    print(analyzer.generate_report())
