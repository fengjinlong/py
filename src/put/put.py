#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期权防御策略量化分析器
基于不同期限期权数据，分析防御性看跌策略的最优方案
包括直接买入、价差组合等策略的Delta、Theta、Vega、IV分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class OptionsDefenseAnalyzer:
    """期权防御策略分析器"""
    
    def __init__(self, data_folder='data', export_folder='export'):
        self.data_folder = data_folder
        self.export_folder = export_folder
        self.spot_price = None
        self.options_data = {}
        self.analysis_results = {}
        
    def load_data(self, spot_price=None):
        """加载期权数据"""
        print("📊 正在加载期权数据...")
        
        # 如果没有提供标的价格，尝试从数据中推断
        if spot_price is None:
            spot_price = self._infer_spot_price()
        
        self.spot_price = spot_price
        print(f"📈 标的价格设定为: ${spot_price:,.2f}")
        
        # 加载不同期限的数据
        file_mapping = {
            '60d': 'BTC-28NOV25-export.csv',   # 约60天
            '90d': 'BTC-26DEC25-export.csv',   # 约90天  
            '180d': 'BTC-27MAR26-export.csv'   # 约180天
        }
        
        for period, filename in file_mapping.items():
            try:
                filepath = f"{self.data_folder}/{filename}"
                df = pd.read_csv(filepath)
                
                # 数据清洗和预处理
                df_clean = self._clean_data(df, period)
                self.options_data[period] = df_clean
                
                print(f"✅ {period} 数据加载完成: {len(df_clean)} 个期权")
                
            except FileNotFoundError:
                print(f"❌ 未找到文件: {filename}")
            except Exception as e:
                print(f"❌ 加载 {filename} 时出错: {e}")
    
    def _infer_spot_price(self):
        """从数据中推断标的价格"""
        # 尝试从第一个文件推断标的价格
        try:
            filepath = f"{self.data_folder}/BTC-26DEC25-export.csv"
            df = pd.read_csv(filepath)
            
            # 寻找ATM期权（Delta接近0.5的看涨期权）
            call_options = df[df['产品'].str.contains('-C')].copy()
            if not call_options.empty:
                # 使用标记价格和Delta来估算标的价格
                atm_calls = call_options[abs(call_options['Δ|增量'] - 0.5) < 0.1]
                if not atm_calls.empty:
                    # 简单估算：标的价格 ≈ 行权价 + 期权价格
                    strike = float(atm_calls.iloc[0]['产品'].split('-')[2])
                    option_price = atm_calls.iloc[0]['标记']
                    estimated_spot = strike + option_price
                    return estimated_spot
        
        except:
            pass
        
        # 如果无法推断，使用默认值
        return 60000.0
    
    def _clean_data(self, df, period):
        """数据清洗和预处理"""
        # 重命名列以统一格式
        column_mapping = {
            '产品': 'symbol',
            '买价': 'bid',
            '卖价': 'ask', 
            '标记': 'mark',
            'IV 报价': 'iv_bid',
            'IV 询价': 'iv_ask',
            'Δ|增量': 'delta',
            'Theta': 'theta',
            'Vega': 'vega',
            'Gamma': 'gamma'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 处理空值和特殊字符
        df = df.replace(['-', ''], np.nan)
        
        # 提取行权价和期权类型
        strike_type = df['symbol'].str.extract(r'-(\d+)-([CP])')
        df['strike'] = pd.to_numeric(strike_type[0], errors='coerce')
        df['option_type'] = strike_type[1]
        
        # 转换数值列
        numeric_columns = ['bid', 'ask', 'mark', 'iv_bid', 'iv_ask', 'delta', 'theta', 'vega', 'gamma']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 过滤有效数据
        df = df.dropna(subset=['strike', 'option_type'])
        df = df.dropna(subset=['delta', 'theta', 'vega'], how='all')
        
        # 只保留看跌期权
        df = df[df['option_type'] == 'P'].copy()
        
        if df.empty:
            return df
        
        # 计算中间价
        df['mid_price'] = (df['bid'] + df['ask']) / 2
        df['mid_price'] = df['mid_price'].fillna(df['mark'])
        
        # 计算隐含波动率中间价
        df['iv_mid'] = (df['iv_bid'] + df['iv_ask']) / 2
        df['iv_mid'] = df['iv_mid'].fillna(df['iv_bid'])
        
        # 计算moneyness
        df['moneyness'] = df['strike'] / self.spot_price
        
        # 计算时间价值
        df['intrinsic_value'] = np.maximum(df['strike'] - self.spot_price, 0)
        df['time_value'] = df['mid_price'] - df['intrinsic_value']
        
        # 添加期限标识
        df['period'] = period
        
        # 计算关键指标
        df['vega_theta_ratio'] = df['vega'] / abs(df['theta'])
        df['delta_abs'] = abs(df['delta'])
        
        return df
    
    def calculate_metrics(self):
        """计算分析指标"""
        print("🧮 正在计算分析指标...")
        
        for period, df in self.options_data.items():
            # 计算性价比评分
            df['cost_effectiveness'] = df['vega'] / abs(df['theta']) * (1 / df['iv_mid'])
            
            # 计算IV分位数
            df['iv_percentile'] = df['iv_mid'].rank(pct=True)
            
            # 计算防御性评分（Delta在-0.3到-0.5之间为最佳）
            df['defense_score'] = np.where(
                (df['delta'] >= -0.5) & (df['delta'] <= -0.3),
                1.0,
                np.exp(-((df['delta'] + 0.4) ** 2) / 0.1)
            )
            
            # 综合评分
            df['composite_score'] = (
                df['cost_effectiveness'] * 0.4 +
                df['defense_score'] * 0.3 +
                (1 - df['iv_percentile']) * 0.3
            )
            
            self.options_data[period] = df
    
    def analyze_strategies(self):
        """分析不同策略"""
        print("📋 正在分析策略...")
        
        strategies = {}
        
        for period, df in self.options_data.items():
            # 策略1: 单独买入看跌期权
            single_put = self._analyze_single_put(df)
            
            # 策略2: 看跌价差策略
            bear_spread = self._analyze_bear_put_spread(df)
            
            strategies[period] = {
                'single_put': single_put,
                'bear_spread': bear_spread
            }
        
        self.analysis_results = strategies
    
    def _analyze_single_put(self, df):
        """分析单独买入看跌期权策略"""
        # 寻找最佳期权
        if df.empty or 'composite_score' not in df.columns:
            return None
        
        best_idx = df['composite_score'].idxmax()
        if pd.isna(best_idx):
            return None
            
        best_option = df.loc[best_idx]
        
        return {
            'strike': best_option['strike'],
            'delta': best_option['delta'],
            'theta': best_option['theta'],
            'vega': best_option['vega'],
            'iv': best_option['iv_mid'],
            'price': best_option['mid_price'],
            'vega_theta_ratio': best_option['vega_theta_ratio'],
            'cost_effectiveness': best_option['cost_effectiveness'],
            'defense_score': best_option['defense_score']
        }
    
    def _analyze_bear_put_spread(self, df):
        """分析看跌价差策略"""
        # 寻找ATM或略OTM的看跌期权作为买入端
        atm_puts = df[(df['moneyness'] >= 0.95) & (df['moneyness'] <= 1.05)]
        
        if atm_puts.empty:
            return None
        
        best_spreads = []
        
        for _, long_put in atm_puts.iterrows():
            # 寻找更低行权价的看跌期权作为卖出端
            short_puts = df[df['strike'] < long_put['strike']]
            
            if short_puts.empty:
                continue
            
            # 选择最佳卖出端期权
            if not short_puts.empty and 'composite_score' in short_puts.columns:
                best_short_idx = short_puts['composite_score'].idxmax()
                if pd.notna(best_short_idx):
                    best_short = short_puts.loc[best_short_idx]
                else:
                    continue
            else:
                continue
            
            # 计算价差组合指标
            spread_delta = long_put['delta'] - best_short['delta']
            spread_theta = long_put['theta'] - best_short['theta']
            spread_vega = long_put['vega'] - best_short['vega']
            spread_cost = long_put['mid_price'] - best_short['mid_price']
            
            spread_metrics = {
                'long_strike': long_put['strike'],
                'short_strike': best_short['strike'],
                'delta': spread_delta,
                'theta': spread_theta,
                'vega': spread_vega,
                'cost': spread_cost,
                'vega_theta_ratio': spread_vega / abs(spread_theta) if spread_theta != 0 else 0,
                'cost_effectiveness': spread_vega / abs(spread_theta) * (1 / ((long_put['iv_mid'] + best_short['iv_mid']) / 2)) if spread_theta != 0 else 0
            }
            
            best_spreads.append(spread_metrics)
        
        if not best_spreads:
            return None
        
        # 返回最佳价差组合
        return max(best_spreads, key=lambda x: x['cost_effectiveness'])
    
    def generate_visualizations(self):
        """生成可视化图表"""
        print("📊 正在生成可视化图表...")
        
        # 创建图表
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('期权防御策略分析报告', fontsize=16, fontweight='bold')
        
        # 1. IV Smile 对比
        self._plot_iv_smile(axes[0, 0])
        
        # 2. Vega/Theta 比值对比
        self._plot_vega_theta_ratio(axes[0, 1])
        
        # 3. 性价比评分对比
        self._plot_cost_effectiveness(axes[0, 2])
        
        # 4. Delta分布对比
        self._plot_delta_distribution(axes[1, 0])
        
        # 5. 策略对比
        self._plot_strategy_comparison(axes[1, 1])
        
        # 6. 期限对比
        self._plot_period_comparison(axes[1, 2])
        
        plt.tight_layout()
        plt.savefig(f'{self.export_folder}/options_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_iv_smile(self, ax):
        """绘制IV Smile"""
        for period, df in self.options_data.items():
            ax.plot(df['strike'], df['iv_mid'], 'o-', label=f'{period}', alpha=0.7)
        
        ax.axvline(self.spot_price, color='red', linestyle='--', alpha=0.5, label='标的价格')
        ax.set_xlabel('行权价')
        ax.set_ylabel('隐含波动率 (%)')
        ax.set_title('IV Smile 对比')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_vega_theta_ratio(self, ax):
        """绘制Vega/Theta比值"""
        for period, df in self.options_data.items():
            ax.plot(df['strike'], df['vega_theta_ratio'], 'o-', label=f'{period}', alpha=0.7)
        
        ax.axvline(self.spot_price, color='red', linestyle='--', alpha=0.5, label='标的价格')
        ax.set_xlabel('行权价')
        ax.set_ylabel('Vega/Theta 比值')
        ax.set_title('Vega/Theta 比值对比')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_cost_effectiveness(self, ax):
        """绘制性价比评分"""
        for period, df in self.options_data.items():
            ax.plot(df['strike'], df['cost_effectiveness'], 'o-', label=f'{period}', alpha=0.7)
        
        ax.axvline(self.spot_price, color='red', linestyle='--', alpha=0.5, label='标的价格')
        ax.set_xlabel('行权价')
        ax.set_ylabel('性价比评分')
        ax.set_title('性价比评分对比')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_delta_distribution(self, ax):
        """绘制Delta分布"""
        for period, df in self.options_data.items():
            ax.hist(df['delta'], bins=20, alpha=0.6, label=f'{period}')
        
        ax.axvline(-0.3, color='green', linestyle='--', alpha=0.7, label='最佳防御区间')
        ax.axvline(-0.5, color='green', linestyle='--', alpha=0.7)
        ax.set_xlabel('Delta')
        ax.set_ylabel('频次')
        ax.set_title('Delta分布对比')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_strategy_comparison(self, ax):
        """绘制策略对比"""
        periods = list(self.analysis_results.keys())
        single_put_ratios = [self.analysis_results[p]['single_put']['vega_theta_ratio'] for p in periods]
        bear_spread_ratios = [self.analysis_results[p]['bear_spread']['vega_theta_ratio'] if self.analysis_results[p]['bear_spread'] else 0 for p in periods]
        
        x = np.arange(len(periods))
        width = 0.35
        
        ax.bar(x - width/2, single_put_ratios, width, label='单买Put', alpha=0.8)
        ax.bar(x + width/2, bear_spread_ratios, width, label='Bear Put Spread', alpha=0.8)
        
        ax.set_xlabel('期限')
        ax.set_ylabel('Vega/Theta 比值')
        ax.set_title('策略Vega/Theta比值对比')
        ax.set_xticks(x)
        ax.set_xticklabels(periods)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_period_comparison(self, ax):
        """绘制期限对比"""
        periods = list(self.analysis_results.keys())
        avg_iv = [self.options_data[p]['iv_mid'].mean() for p in periods]
        avg_vega_theta = [self.options_data[p]['vega_theta_ratio'].mean() for p in periods]
        
        ax2 = ax.twinx()
        
        line1 = ax.plot(periods, avg_iv, 'o-', color='blue', label='平均IV')
        line2 = ax2.plot(periods, avg_vega_theta, 's-', color='red', label='平均Vega/Theta')
        
        ax.set_xlabel('期限')
        ax.set_ylabel('平均IV (%)', color='blue')
        ax2.set_ylabel('平均Vega/Theta比值', color='red')
        ax.set_title('期限对比分析')
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left')
        ax.grid(True, alpha=0.3)
    
    def generate_report(self):
        """生成分析报告"""
        print("📝 正在生成分析报告...")
        
        # 创建汇总表格
        summary_data = []
        
        for period, results in self.analysis_results.items():
            single_put = results['single_put']
            bear_spread = results['bear_spread']
            
            summary_data.append({
                '期限': period,
                '策略类型': '单买Put',
                '行权价': single_put['strike'],
                'Delta': f"{single_put['delta']:.3f}",
                'Theta': f"{single_put['theta']:.3f}",
                'Vega': f"{single_put['vega']:.3f}",
                'IV': f"{single_put['iv']:.1f}%",
                'Vega/Theta': f"{single_put['vega_theta_ratio']:.2f}",
                '性价比': f"{single_put['cost_effectiveness']:.2f}"
            })
            
            if bear_spread:
                summary_data.append({
                    '期限': period,
                    '策略类型': 'Bear Put Spread',
                    '行权价': f"{bear_spread['long_strike']}/{bear_spread['short_strike']}",
                    'Delta': f"{bear_spread['delta']:.3f}",
                    'Theta': f"{bear_spread['theta']:.3f}",
                    'Vega': f"{bear_spread['vega']:.3f}",
                    'IV': f"{(single_put['iv'] + bear_spread.get('iv', single_put['iv']))/2:.1f}%",
                    'Vega/Theta': f"{bear_spread['vega_theta_ratio']:.2f}",
                    '性价比': f"{bear_spread['cost_effectiveness']:.2f}"
                })
        
        summary_df = pd.DataFrame(summary_data)
        
        # 保存到CSV
        summary_df.to_csv(f'{self.export_folder}/options_analysis_summary.csv', index=False, encoding='utf-8-sig')
        
        # 生成文字报告
        self._generate_text_report(summary_df)
        
        return summary_df
    
    def _generate_text_report(self, summary_df):
        """生成文字分析报告"""
        report = []
        report.append("=" * 60)
        report.append("期权防御策略量化分析报告")
        report.append("=" * 60)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"标的价格: ${self.spot_price:,.2f}")
        report.append("")
        
        # 最佳策略推荐
        if not summary_df.empty:
            best_strategy = summary_df.loc[summary_df['性价比'].astype(float).idxmax()]
            report.append("🎯 最佳策略推荐:")
            report.append(f"   期限: {best_strategy['期限']}")
            report.append(f"   策略: {best_strategy['策略类型']}")
            report.append(f"   行权价: {best_strategy['行权价']}")
            report.append(f"   性价比评分: {best_strategy['性价比']}")
            report.append("")
        else:
            report.append("🎯 最佳策略推荐:")
            report.append("   暂无有效数据进行分析")
            report.append("")
        
        # 各期限分析
        report.append("📊 各期限分析:")
        for period in ['60d', '90d', '180d']:
            if period in self.options_data:
                df = self.options_data[period]
                avg_iv = df['iv_mid'].mean()
                avg_vega_theta = df['vega_theta_ratio'].mean()
                best_defense = df.loc[df['defense_score'].idxmax()]
                
                report.append(f"   {period}:")
                report.append(f"     平均IV: {avg_iv:.1f}%")
                report.append(f"     平均Vega/Theta: {avg_vega_theta:.2f}")
                report.append(f"     最佳防御期权Delta: {best_defense['delta']:.3f}")
                report.append("")
        
        # 策略建议
        report.append("💡 策略建议:")
        report.append("   1. 防御性目标: Delta在-0.3到-0.5之间")
        report.append("   2. 时间损耗: 选择Vega/Theta比值较高的期权")
        report.append("   3. 波动率: 在IV相对低位时入场")
        report.append("   4. 成本控制: 考虑使用价差策略降低净成本")
        report.append("")
        
        # 风险提示
        report.append("⚠️ 风险提示:")
        report.append("   1. 期权交易存在时间价值衰减风险")
        report.append("   2. 隐含波动率变化可能影响期权价格")
        report.append("   3. 建议设置止损和仓位管理")
        report.append("   4. 定期调整策略以适应市场变化")
        
        report_text = "\n".join(report)
        
        # 保存报告
        with open(f'{self.export_folder}/analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
    
    def run_analysis(self, spot_price=None):
        """运行完整分析"""
        print("🚀 开始期权防御策略分析...")
        print("=" * 50)
        
        # 1. 加载数据
        self.load_data(spot_price)
        
        # 2. 计算指标
        self.calculate_metrics()
        
        # 3. 分析策略
        self.analyze_strategies()
        
        # 4. 生成可视化
        self.generate_visualizations()
        
        # 5. 生成报告
        summary_df = self.generate_report()
        
        print("=" * 50)
        print("✅ 分析完成！")
        print(f"📁 结果已保存到 {self.export_folder} 文件夹")
        
        return summary_df

def main():
    """主函数"""
    # 创建分析器
    analyzer = OptionsDefenseAnalyzer()
    
    # 运行分析（可以手动设置标的价格）
    # analyzer.run_analysis(spot_price=60000)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
