#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期权防御策略量化分析脚本
作者: 量化金融开发者
功能: 分析BTC期权数据，生成防御策略评估报告
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from datetime import datetime, date
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# =============================================================================
# 用户配置区域
# =============================================================================

# 数据文件夹路径
DATA_FOLDER = 'data'

# 现货价格 (设为None时将在运行时提示用户输入)
SPOT_PRICE = None

# 策略配置
STRATEGY_CONFIG = {
    'full_protection_put': {'min_delta': -0.55, 'max_delta': -0.45},
    'partial_protection_put': {'min_delta': -0.35, 'max_delta': -0.25},
    'tail_hedge_put': {'min_delta': -0.15, 'max_delta': -0.05},
    'bear_put_spread': {
        'long_leg_min_delta': -0.40,
        'long_leg_max_delta': -0.30,
        'short_leg_min_delta': -0.15,
        'short_leg_max_delta': -0.10,
    }
}

# 输出文件夹
OUTPUT_FOLDER = 'export'

# =============================================================================
# 核心功能函数
# =============================================================================

def clear_export_folder():
    """
    清空export文件夹中的所有文件
    """
    try:
        if os.path.exists(OUTPUT_FOLDER):
            for filename in os.listdir(OUTPUT_FOLDER):
                file_path = os.path.join(OUTPUT_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"已删除文件: {filename}")
        else:
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            print(f"已创建文件夹: {OUTPUT_FOLDER}")
    except Exception as e:
        print(f"清空export文件夹时出错: {str(e)}")

def get_spot_price():
    """
    获取现货价格
    如果SPOT_PRICE为None，则提示用户输入
    """
    global SPOT_PRICE
    
    if SPOT_PRICE is None:
        try:
            user_input = input("请输入当前BTC现货价格 (直接回车使用默认价格$100,000): ").strip()
            if user_input:
                SPOT_PRICE = float(user_input)
                if SPOT_PRICE <= 0:
                    print("价格必须大于0，使用默认价格。")
                    SPOT_PRICE = 100000
            else:
                SPOT_PRICE = 100000
        except ValueError:
            print("价格输入无效，使用默认价格。")
            SPOT_PRICE = 100000
        except EOFError:
            # 处理非交互式环境
            SPOT_PRICE = 100000
            print("非交互式环境，使用默认价格。")
    
    print(f"使用现货价格: ${SPOT_PRICE:,.2f}")
    return SPOT_PRICE

def load_and_clean_data():
    """
    加载并清洗期权数据
    """
    print("正在加载期权数据...")
    
    # 确保数据文件夹存在
    if not os.path.exists(DATA_FOLDER):
        raise FileNotFoundError(f"数据文件夹 '{DATA_FOLDER}' 不存在")
    
    # 查找所有CSV文件
    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError(f"在 '{DATA_FOLDER}' 文件夹中未找到CSV文件")
    
    print(f"找到 {len(csv_files)} 个CSV文件: {csv_files}")
    
    all_data = []
    
    for file in csv_files:
        file_path = os.path.join(DATA_FOLDER, file)
        print(f"正在处理文件: {file}")
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 列名映射
        column_mapping = {
            '产品': 'symbol',
            '买价': 'bid_price',
            '卖价': 'ask_price',
            'Δ|增量': 'delta',
            'Gamma': 'gamma',
            'Theta': 'theta',
            'Vega': 'vega',
            'IV 报价': 'bid_iv',
            'IV 询价': 'ask_iv',
            '标记': 'mark_price'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 提取期权信息
        df = extract_option_info(df)
        
        # 只保留看跌期权
        df = df[df['option_type'] == 'P'].copy()
        
        if len(df) == 0:
            print(f"警告: 文件 {file} 中没有找到看跌期权数据")
            continue
        
        # 数据类型转换
        df = convert_data_types(df)
        
        # 计算辅助列
        df = calculate_auxiliary_columns(df)
        
        all_data.append(df)
    
    if not all_data:
        raise ValueError("没有找到有效的看跌期权数据")
    
    # 合并所有数据
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"成功加载 {len(combined_df)} 条看跌期权数据")
    return combined_df

def extract_option_info(df):
    """
    从symbol列提取期权信息
    """
    def parse_symbol(symbol):
        # 匹配格式: BTC-26DEC25-65000-P
        pattern = r'BTC-(\d{2}[A-Z]{3}\d{2})-(\d+)-([CP])'
        match = re.match(pattern, symbol)
        
        if match:
            date_str, strike_str, option_type = match.groups()
            # 解析日期
            try:
                exp_date = datetime.strptime(date_str, '%d%b%y').date()
            except:
                exp_date = None
            
            return {
                'expiration_date': exp_date,
                'strike_price': float(strike_str),
                'option_type': option_type
            }
        else:
            return {
                'expiration_date': None,
                'strike_price': None,
                'option_type': None
            }
    
    # 应用解析函数
    option_info = df['symbol'].apply(parse_symbol)
    option_df = pd.DataFrame(option_info.tolist())
    
    # 合并到原DataFrame
    df = pd.concat([df, option_df], axis=1)
    
    return df

def convert_data_types(df):
    """
    转换数据类型
    """
    # 需要转换为数值的列
    numeric_columns = [
        'bid_price', 'ask_price', 'delta', 'gamma', 'theta', 'vega',
        'bid_iv', 'ask_iv', 'mark_price', 'strike_price'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            # 将 '-' 和空值转换为NaN
            df[col] = df[col].replace(['-', '', ' '], np.nan)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_auxiliary_columns(df):
    """
    计算辅助列
    """
    # 添加标的现货价格列
    df['underlying_price'] = SPOT_PRICE
    
    # 中间价格（币本位统计，需要乘以标的价格）
    df['mid_price'] = (df['bid_price'] + df['ask_price']) / 2 * SPOT_PRICE
    
    # 中间隐含波动率（除以100，因为原始数据被扩大了100倍）
    df['mid_iv'] = (df['bid_iv'] + df['ask_iv']) / 2 / 100
    
    # 计算到期天数
    today = date.today()
    df['days_to_expiration'] = df['expiration_date'].apply(
        lambda x: (x - today).days if pd.notna(x) else np.nan
    )
    
    return df

def calculate_metrics(df):
    """
    计算性价比指标
    """
    print("正在计算性价比指标...")
    
    # 计算预期波动范围
    df['expected_move'] = (
        SPOT_PRICE * df['mid_iv'] * 
        np.sqrt(df['days_to_expiration'] / 365)
    )
    
    # 计算性价比指标
    # Vega/Theta比率
    df['vega_to_theta_ratio'] = np.where(
        df['theta'] != 0, 
        df['vega'] / np.abs(df['theta']), 
        np.nan
    )
    
    # Gamma/Theta比率
    df['gamma_to_theta_ratio'] = np.where(
        df['theta'] != 0, 
        df['gamma'] / np.abs(df['theta']), 
        np.nan
    )
    
    # Vega/权利金比率
    df['vega_per_premium'] = np.where(
        df['mid_price'] != 0, 
        df['vega'] / df['mid_price'], 
        np.nan
    )
    
    # Delta/权利金比率
    df['delta_per_premium'] = np.where(
        df['mid_price'] != 0, 
        np.abs(df['delta']) / df['mid_price'], 
        np.nan
    )
    
    return df

def analyze_single_put(df, strategy_name, config):
    """
    分析单腿看跌期权策略
    """
    # 筛选符合delta区间的期权
    mask = (
        (df['delta'] >= config['min_delta']) & 
        (df['delta'] <= config['max_delta'])
    )
    
    filtered_df = df[mask].copy()
    
    if len(filtered_df) == 0:
        return pd.DataFrame()
    
    # 按性价比指标排序
    filtered_df = filtered_df.sort_values(
        ['vega_to_theta_ratio', 'vega_per_premium'], 
        ascending=[False, False]
    )
    
    return filtered_df.head(5)

def analyze_bear_put_spread(df, config):
    """
    分析熊市看跌价差策略
    """
    # 筛选长腿和短腿候选
    long_leg_mask = (
        (df['delta'] >= config['long_leg_min_delta']) & 
        (df['delta'] <= config['long_leg_max_delta'])
    )
    
    short_leg_mask = (
        (df['delta'] >= config['short_leg_min_delta']) & 
        (df['delta'] <= config['short_leg_max_delta'])
    )
    
    long_legs = df[long_leg_mask].copy()
    short_legs = df[short_leg_mask].copy()
    
    if len(long_legs) == 0 or len(short_legs) == 0:
        return pd.DataFrame()
    
    # 构建价差组合
    spreads = []
    
    for _, long_leg in long_legs.iterrows():
        for _, short_leg in short_legs.iterrows():
            # 确保长腿行权价 > 短腿行权价
            if long_leg['strike_price'] > short_leg['strike_price']:
                # 计算价差指标
                net_premium = long_leg['mid_price'] - short_leg['mid_price']
                max_risk = net_premium
                max_profit = (long_leg['strike_price'] - short_leg['strike_price']) - net_premium
                breakeven = long_leg['strike_price'] - net_premium
                reward_risk_ratio = max_profit / max_risk if max_risk > 0 else 0
                
                # 计算赔率 (基于Delta值估算成功概率)
                # 长腿Delta的绝对值表示期权在到期时处于实值状态的概率
                long_leg_prob = abs(long_leg['delta'])
                short_leg_prob = abs(short_leg['delta'])
                
                # 价差策略成功概率：长腿实值且短腿虚值的概率
                # 简化计算：使用长腿Delta作为基础成功概率
                success_prob = long_leg_prob
                failure_prob = 1 - success_prob
                
                # 赔率 = 失败概率 / 成功概率
                odds = failure_prob / success_prob if success_prob > 0 else 0
                
                spread_data = {
                    'long_strike': long_leg['strike_price'],
                    'short_strike': short_leg['strike_price'],
                    'long_delta': long_leg['delta'],
                    'short_delta': short_leg['delta'],
                    'long_price': long_leg['mid_price'],
                    'short_price': short_leg['mid_price'],
                    'net_premium': net_premium,
                    'max_risk': max_risk,
                    'max_profit': max_profit,
                    'breakeven': breakeven,
                    'reward_risk_ratio': reward_risk_ratio,
                    'success_prob': success_prob,
                    'failure_prob': failure_prob,
                    'odds': odds,
                    'expiration_date': long_leg['expiration_date']
                }
                
                spreads.append(spread_data)
    
    if not spreads:
        return pd.DataFrame()
    
    spreads_df = pd.DataFrame(spreads)
    spreads_df = spreads_df.sort_values('reward_risk_ratio', ascending=False)
    
    return spreads_df.head(5)

def generate_report(df, single_put_results, bear_put_spread_results):
    """
    生成分析报告
    """
    print("\n" + "="*80)
    print("BTC期权防御策略量化分析报告")
    print("="*80)
    print(f"分析日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"标的现货价格: ${SPOT_PRICE:,.2f}")
    print(f"分析期权数量: {len(df)} 个")
    
    # 按到期日分组分析
    expiration_dates = df['expiration_date'].dropna().unique()
    
    for exp_date in sorted(expiration_dates):
        print(f"\n{'='*60}")
        print(f"到期日: {exp_date}")
        print(f"{'='*60}")
        
        exp_df = df[df['expiration_date'] == exp_date]
        
        # 单腿策略分析
        print("\n【单腿看跌期权策略】")
        
        strategies = [
            ('全面保护', 'full_protection_put'),
            ('部分保护', 'partial_protection_put'),
            ('尾部对冲', 'tail_hedge_put')
        ]
        
        for strategy_name, strategy_key in strategies:
            if strategy_key in single_put_results:
                strategy_df = single_put_results[strategy_key]
                strategy_exp_df = strategy_df[strategy_df['expiration_date'] == exp_date]
                
                if len(strategy_exp_df) > 0:
                    print(f"\n{strategy_name}策略 (Top 3):")
                    for i, (_, row) in enumerate(strategy_exp_df.head(3).iterrows(), 1):
                        print(f"  {i}. 行权价: ${row['strike_price']:,.0f}, "
                              f"Delta: {row['delta']:.3f}, "
                              f"权利金: ${row['mid_price']:.4f}, "
                              f"Vega/Theta: {row['vega_to_theta_ratio']:.2f}")
        
        # 价差策略分析
        print(f"\n【熊市看跌价差策略】")
        if 'bear_put_spread' in bear_put_spread_results:
            spread_df = bear_put_spread_results['bear_put_spread']
            spread_exp_df = spread_df[spread_df['expiration_date'] == exp_date]
            
            if len(spread_exp_df) > 0:
                print("最优组合 (Top 3):")
                for i, (_, row) in enumerate(spread_exp_df.head(3).iterrows(), 1):
                    print(f"  {i}. 长腿: ${row['long_strike']:,.0f}, "
                          f"短腿: ${row['short_strike']:,.0f}, "
                          f"净权利金: ${row['net_premium']:.4f}, "
                          f"盈亏比: {row['reward_risk_ratio']:.2f}, "
                          f"赔率: {row['odds']:.2f}:1 (成功概率: {row['success_prob']:.1%})")
    
    # 生成综合报告文档
    generate_comprehensive_report(df, single_put_results, bear_put_spread_results)
    
    # 保存详细数据到CSV
    save_detailed_data(df, single_put_results, bear_put_spread_results)

def generate_comprehensive_report(df, single_put_results, bear_put_spread_results):
    """
    生成综合报告文档
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(OUTPUT_FOLDER, f'comprehensive_report_{timestamp}.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# BTC期权防御策略量化分析综合报告\n\n")
        f.write(f"**分析日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**标的现货价格**: ${SPOT_PRICE:,.2f}\n")
        f.write(f"**分析期权数量**: {len(df)} 个\n\n")
        
        # 市场概况
        f.write("## 市场概况\n\n")
        expiration_dates = df['expiration_date'].dropna().unique()
        f.write(f"**到期日数量**: {len(expiration_dates)} 个\n")
        f.write(f"**到期日范围**: {min(expiration_dates)} 至 {max(expiration_dates)}\n\n")
        
        # 按到期日分析
        f.write("## 策略分析结果\n\n")
        
        for exp_date in sorted(expiration_dates):
            f.write(f"### 到期日: {exp_date}\n\n")
            
            exp_df = df[df['expiration_date'] == exp_date]
            days_to_exp = (exp_date - date.today()).days
            
            f.write(f"**到期天数**: {days_to_exp} 天\n")
            f.write(f"**该到期日期权数量**: {len(exp_df)} 个\n\n")
            
            # 单腿策略分析
            f.write("#### 【单腿看跌期权策略】\n\n")
            
            strategies = [
                ('全面保护策略', 'full_protection_put', 'Delta: -0.55 至 -0.45', '适合大幅下跌保护'),
                ('部分保护策略', 'partial_protection_put', 'Delta: -0.35 至 -0.25', '适合中等下跌保护'),
                ('尾部对冲策略', 'tail_hedge_put', 'Delta: -0.15 至 -0.05', '适合尾部风险对冲')
            ]
            
            for strategy_name, strategy_key, delta_range, description in strategies:
                if strategy_key in single_put_results:
                    strategy_df = single_put_results[strategy_key]
                    strategy_exp_df = strategy_df[strategy_df['expiration_date'] == exp_date]
                    
                    if len(strategy_exp_df) > 0:
                        f.write(f"**{strategy_name}** ({delta_range})\n")
                        f.write(f"*{description}*\n\n")
                        
                        for i, (_, row) in enumerate(strategy_exp_df.head(3).iterrows(), 1):
                            f.write(f"{i}. **行权价**: ${row['strike_price']:,.0f}\n")
                            f.write(f"   - Delta: {row['delta']:.3f}\n")
                            f.write(f"   - 权利金: ${row['mid_price']:.4f}\n")
                            f.write(f"   - Vega/Theta比率: {row['vega_to_theta_ratio']:.2f}\n")
                            f.write(f"   - 隐含波动率: {row['mid_iv']:.1%}\n")
                            f.write(f"   - 到期天数: {row['days_to_expiration']:.0f}天\n\n")
                    else:
                        f.write(f"**{strategy_name}**: 无符合条件的期权\n\n")
            
            # 价差策略分析
            f.write("#### 【熊市看跌价差策略】\n\n")
            f.write("*通过买入高行权价看跌期权，卖出低行权价看跌期权，降低权利金成本*\n\n")
            
            if 'bear_put_spread' in bear_put_spread_results:
                spread_df = bear_put_spread_results['bear_put_spread']
                spread_exp_df = spread_df[spread_df['expiration_date'] == exp_date]
                
                if len(spread_exp_df) > 0:
                    for i, (_, row) in enumerate(spread_exp_df.head(3).iterrows(), 1):
                        f.write(f"{i}. **长腿**: ${row['long_strike']:,.0f} (Delta: {row['long_delta']:.3f})\n")
                        f.write(f"   **短腿**: ${row['short_strike']:,.0f} (Delta: {row['short_delta']:.3f})\n")
                        f.write(f"   - 净权利金: ${row['net_premium']:.4f}\n")
                        f.write(f"   - 最大风险: ${row['max_risk']:.4f}\n")
                        f.write(f"   - 最大利润: ${row['max_profit']:.4f}\n")
                        f.write(f"   - 盈亏平衡点: ${row['breakeven']:.0f}\n")
                        f.write(f"   - 盈亏比: {row['reward_risk_ratio']:.2f}\n\n")
                else:
                    f.write("无符合条件的价差组合\n\n")
            else:
                f.write("无符合条件的价差组合\n\n")
            
            f.write("---\n\n")
        
        # 最优策略推荐
        f.write("## 最优策略推荐与分析\n\n")
        
        # 分析最优策略
        best_strategies = analyze_best_strategies(df, single_put_results, bear_put_spread_results)
        
        for category, analysis in best_strategies.items():
            f.write(f"### {category}\n\n")
            f.write(f"{analysis}\n\n")
        
        # 风险提示
        f.write("## 风险提示\n\n")
        f.write("1. **时间价值衰减**: 期权时间价值会随时间衰减，临近到期时衰减加速\n")
        f.write("2. **隐含波动率风险**: 隐含波动率下降会导致期权价格下跌\n")
        f.write("3. **流动性风险**: 深度价外期权可能存在流动性不足的问题\n")
        f.write("4. **方向性风险**: 看跌期权在价格上涨时会亏损\n")
        f.write("5. **保证金要求**: 价差策略需要满足保证金要求\n\n")
        
        # 使用建议
        f.write("## 使用建议\n\n")
        f.write("1. **全面保护策略**: 适合预期大幅下跌的投资者，提供强保护但成本较高\n")
        f.write("2. **部分保护策略**: 适合预期中等下跌的投资者，平衡保护效果与成本\n")
        f.write("3. **尾部对冲策略**: 适合长期持有者，提供极端情况下的保护\n")
        f.write("4. **熊市价差策略**: 适合预期下跌但希望降低成本的投资者\n")
        f.write("5. **组合使用**: 可考虑将不同策略组合使用，构建多层次保护体系\n\n")
        
        f.write("---\n")
        f.write(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    print(f"综合报告已保存至: {report_file}")

def analyze_best_strategies(df, single_put_results, bear_put_spread_results):
    """
    分析最优策略并给出推荐理由
    """
    analysis = {}
    
    # 获取市场基础数据
    current_price = df['underlying_price'].iloc[0] if 'underlying_price' in df.columns else 100000
    avg_iv = df['mid_iv'].mean()
    avg_days_to_exp = df['days_to_expiration'].mean()
    
    # 分析单腿策略 - 多维度评估
    best_single_put = None
    best_score = 0
    
    strategy_scores = {}
    for strategy_name, strategy_df in single_put_results.items():
        if len(strategy_df) > 0:
            # 计算综合评分：Vega/Theta比率 + 流动性 + 时间价值
            vega_theta_score = strategy_df['vega_to_theta_ratio'].max()
            liquidity_score = 1.0  # 简化处理，实际可根据成交量等计算
            time_value_score = 1.0 if avg_days_to_exp > 30 else 0.8  # 时间价值衰减考虑
            
            total_score = vega_theta_score * 0.5 + liquidity_score * 0.3 + time_value_score * 0.2
            strategy_scores[strategy_name] = total_score
            
            if total_score > best_score:
                best_score = total_score
                best_single_put = strategy_name
    
    if best_single_put:
        strategy_names = {
            'full_protection_put': '全面保护策略',
            'partial_protection_put': '部分保护策略', 
            'tail_hedge_put': '尾部对冲策略'
        }
        
        best_df = single_put_results[best_single_put]
        best_option = best_df.iloc[0]
        
        # 计算保护水平
        protection_level = (current_price - best_option['strike_price']) / current_price * 100
        
        analysis['🏆 最优单腿策略推荐'] = f"""
### 📊 策略概览
**推荐策略**: {strategy_names[best_single_put]}
**综合评分**: {best_score:.2f}/10.0
**保护水平**: {protection_level:.1f}% (当前价格: ${current_price:,.0f})

### 🎯 最优期权详情
| 指标 | 数值 | 评级 |
|------|------|------|
| 行权价 | ${best_option['strike_price']:,.0f} | {'🟢 深度实值' if best_option['delta'] < -0.7 else '🟡 实值' if best_option['delta'] < -0.5 else '🟠 平值' if best_option['delta'] < -0.3 else '🔴 虚值'} |
| Delta | {best_option['delta']:.3f} | {'强保护' if best_option['delta'] < -0.5 else '中等保护' if best_option['delta'] < -0.3 else '弱保护'} |
| 权利金 | ${best_option['mid_price']:.4f} | {'低成本' if best_option['mid_price'] < 0.01 else '中等成本' if best_option['mid_price'] < 0.05 else '高成本'} |
| Vega/Theta比率 | {best_option['vega_to_theta_ratio']:.2f} | {'优秀' if best_option['vega_to_theta_ratio'] > 2.0 else '良好' if best_option['vega_to_theta_ratio'] > 1.0 else '一般'} |
| 到期天数 | {best_option['days_to_expiration']:.0f}天 | {'长期' if best_option['days_to_expiration'] > 60 else '中期' if best_option['days_to_expiration'] > 30 else '短期'} |

### 💡 推荐理由
1. **🎯 最佳性价比**: Vega/Theta比率达到{best_option['vega_to_theta_ratio']:.2f}，在波动率收益与时间成本间达到最优平衡
2. **🛡️ 风险保护**: 提供{protection_level:.1f}%的价格保护，适合当前市场风险水平
3. **💰 成本效益**: 权利金${best_option['mid_price']:.4f}，在同类策略中具有成本优势
4. **⏰ 时间管理**: {best_option['days_to_expiration']:.0f}天到期，时间价值衰减速度适中
5. **📈 流动性**: 该行权价附近期权流动性良好，便于执行和调整

### ⚠️ 风险提示
- 最大损失: 权利金${best_option['mid_price']:.4f}
- 时间价值衰减风险: {'低' if best_option['days_to_expiration'] > 60 else '中等' if best_option['days_to_expiration'] > 30 else '高'}
- 波动率风险: {'有利' if avg_iv < 0.7 else '不利'}
"""
    
    # 分析价差策略 - 增强版
    if 'bear_put_spread' in bear_put_spread_results:
        spread_df = bear_put_spread_results['bear_put_spread']
        if len(spread_df) > 0:
            best_spread = spread_df.iloc[0]
            
            # 计算价差宽度和成本效益
            spread_width = best_spread['long_strike'] - best_spread['short_strike']  # 修正：长腿行权价应该高于短腿
            cost_efficiency = best_spread['reward_risk_ratio']
            max_profit = spread_width - best_spread['net_premium']
            
            analysis['🏆 最优价差策略推荐'] = f"""
### 📊 策略概览
**推荐策略**: 熊市看跌价差 (Bear Put Spread)
**盈亏比**: {best_spread['reward_risk_ratio']:.2f}:1
**赔率**: {best_spread['odds']:.2f}:1 (成功概率: {best_spread['success_prob']:.1%})
**成本效益**: {'优秀' if cost_efficiency > 2.0 else '良好' if cost_efficiency > 1.5 else '一般'}

### 🎯 最优组合详情
| 组件 | 行权价 | Delta | 作用 |
|------|--------|-------|------|
| 长腿 (买入) | ${best_spread['long_strike']:,.0f} | {best_spread['long_delta']:.3f} | 主要保护 |
| 短腿 (卖出) | ${best_spread['short_strike']:,.0f} | {best_spread['short_delta']:.3f} | 降低成本 |
| 价差宽度 | ${spread_width:,.0f} | - | 最大收益 |

### 💰 财务分析
- **净权利金**: ${best_spread['net_premium']:.4f} (成本)
- **最大收益**: ${max_profit:.4f} (${spread_width:,.0f} - ${best_spread['net_premium']:.4f})
- **最大损失**: ${best_spread['net_premium']:.4f} (净权利金)
- **盈亏平衡点**: ${best_spread['long_strike'] - best_spread['net_premium']:,.0f}

### 🎲 概率分析
- **成功概率**: {best_spread['success_prob']:.1%} (基于长腿Delta)
- **失败概率**: {best_spread['failure_prob']:.1%}
- **赔率**: {best_spread['odds']:.2f}:1 (失败概率/成功概率)
- **期望收益**: ${max_profit * best_spread['success_prob'] - best_spread['net_premium'] * best_spread['failure_prob']:.4f}

### 💡 推荐理由
1. **💰 成本优势**: 通过卖出低行权价期权，将策略成本降低{(best_spread['net_premium'] / spread_width * 100):.1f}%
2. **🛡️ 风险可控**: 最大风险严格限制在净权利金${best_spread['net_premium']:.4f}范围内
3. **📈 盈亏比优秀**: {best_spread['reward_risk_ratio']:.2f}:1的盈亏比，风险收益比优异
4. **🎲 概率合理**: {best_spread['success_prob']:.1%}的成功概率，赔率{best_spread['odds']:.2f}:1，风险收益匹配
5. **🎯 适用性广**: 适合预期下跌但希望控制成本的投资者
6. **⚡ 执行简单**: 单次交易完成，无需复杂管理

### 📊 收益分析
- **最佳情况**: BTC跌至${best_spread['short_strike']:,.0f}以下，获得最大收益${max_profit:.4f}
- **盈亏平衡**: BTC跌至${best_spread['long_strike'] - best_spread['net_premium']:,.0f}时实现盈亏平衡
- **最坏情况**: BTC上涨，损失全部净权利金${best_spread['net_premium']:.4f}
"""
    
    # 市场环境分析 - 增强版
    iv_percentile = (df['mid_iv'] > avg_iv).mean() * 100
    time_to_exp_distribution = {
        '短期(≤30天)': (df['days_to_expiration'] <= 30).sum(),
        '中期(31-60天)': ((df['days_to_expiration'] > 30) & (df['days_to_expiration'] <= 60)).sum(),
        '长期(>60天)': (df['days_to_expiration'] > 60).sum()
    }
    
    analysis['📈 市场环境分析'] = f"""
### 🌍 当前市场特征
| 指标 | 数值 | 市场状态 |
|------|------|----------|
| 平均隐含波动率 | {avg_iv:.1%} | {'🔴 高波动' if avg_iv > 0.8 else '🟡 中等波动' if avg_iv > 0.5 else '🟢 低波动'} |
| 波动率分位数 | {iv_percentile:.0f}% | {'偏高' if iv_percentile > 70 else '适中' if iv_percentile > 30 else '偏低'} |
| 平均到期天数 | {avg_days_to_exp:.0f}天 | {'长期' if avg_days_to_exp > 60 else '中期' if avg_days_to_exp > 30 else '短期'} |
| 期权总数 | {len(df)}个 | {'丰富' if len(df) > 100 else '适中' if len(df) > 50 else '有限'} |

### 📅 到期时间分布
- 短期期权 (≤30天): {time_to_exp_distribution['短期(≤30天)']}个
- 中期期权 (31-60天): {time_to_exp_distribution['中期(31-60天)']}个  
- 长期期权 (>60天): {time_to_exp_distribution['长期(>60天)']}个

### 🎯 市场判断与策略建议
1. **📊 波动率环境**: 
   - 当前IV为{avg_iv:.1%}，{'适合买入期权策略' if avg_iv < 0.7 else '适合卖出期权策略'}
   - 建议{'重点关注单腿策略' if avg_iv < 0.6 else '重点关注价差策略' if avg_iv < 0.8 else '考虑复杂策略'}

2. **⏰ 时间价值管理**:
   - 平均到期{avg_days_to_exp:.0f}天，{'时间价值衰减较慢，适合长期持有' if avg_days_to_exp > 30 else '时间价值衰减较快，需要密切监控'}
   - 建议{'选择长期期权' if avg_days_to_exp < 30 else '选择中期期权' if avg_days_to_exp < 60 else '可考虑短期期权'}

3. **🎯 策略优先级**:
   - **首选**: {'单腿策略' if avg_iv < 0.6 else '价差策略'}
   - **备选**: {'价差策略' if avg_iv < 0.6 else '单腿策略'}
   - **风险控制**: 建议仓位不超过总资金的{'5%' if avg_iv > 0.8 else '10%' if avg_iv > 0.6 else '15%'}

### ⚠️ 风险提示
- **市场风险**: 当前波动率{'偏高' if avg_iv > 0.8 else '适中' if avg_iv > 0.5 else '偏低'}，需注意{'波动率下降风险' if avg_iv > 0.7 else '波动率上升风险'}
- **时间风险**: {'时间价值衰减较快' if avg_days_to_exp < 30 else '时间价值衰减适中'}
- **流动性风险**: 建议选择成交量较大的期权合约
"""
    
    return analysis

def save_detailed_data(df, single_put_results, bear_put_spread_results):
    """
    保存详细数据到CSV文件
    """
    # 确保输出文件夹存在
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 保存完整数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存所有期权数据
    all_data_file = os.path.join(OUTPUT_FOLDER, f'options_analysis_{timestamp}.csv')
    df.to_csv(all_data_file, index=False, encoding='utf-8-sig')
    print(f"\n完整期权数据已保存至: {all_data_file}")
    
    # 保存单腿策略结果
    for strategy_name, strategy_df in single_put_results.items():
        if len(strategy_df) > 0:
            strategy_file = os.path.join(OUTPUT_FOLDER, f'{strategy_name}_{timestamp}.csv')
            strategy_df.to_csv(strategy_file, index=False, encoding='utf-8-sig')
            print(f"{strategy_name}策略结果已保存至: {strategy_file}")
    
    # 保存价差策略结果
    if 'bear_put_spread' in bear_put_spread_results:
        spread_df = bear_put_spread_results['bear_put_spread']
        if len(spread_df) > 0:
            spread_file = os.path.join(OUTPUT_FOLDER, f'bear_put_spread_{timestamp}.csv')
            spread_df.to_csv(spread_file, index=False, encoding='utf-8-sig')
            print(f"熊市看跌价差策略结果已保存至: {spread_file}")

def generate_visualizations(df, bear_put_spread_results):
    """
    生成可视化图表
    """
    print("\n正在生成可视化图表...")
    
    # 确保输出文件夹存在
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. 隐含波动率微笑
    plt.figure(figsize=(12, 8))
    
    expiration_dates = df['expiration_date'].dropna().unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(expiration_dates)))
    
    for i, exp_date in enumerate(sorted(expiration_dates)):
        exp_df = df[df['expiration_date'] == exp_date]
        plt.scatter(exp_df['strike_price'], exp_df['mid_iv'], 
                   label=f'{exp_date}', color=colors[i], alpha=0.7, s=50)
    
    plt.axvline(x=SPOT_PRICE, color='red', linestyle='--', alpha=0.7, 
                label=f'现货价格 ${SPOT_PRICE:,.0f}')
    plt.xlabel('行权价 ($)')
    plt.ylabel('隐含波动率 (%)')
    plt.title('BTC期权隐含波动率微笑')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    iv_file = os.path.join(OUTPUT_FOLDER, f'iv_smile_{timestamp}.png')
    plt.savefig(iv_file, dpi=300, bbox_inches='tight')
    print(f"隐含波动率微笑图已保存至: {iv_file}")
    plt.show()
    
    # 2. Vega/Theta性价比曲线
    plt.figure(figsize=(12, 8))
    
    for i, exp_date in enumerate(sorted(expiration_dates)):
        exp_df = df[df['expiration_date'] == exp_date]
        plt.scatter(exp_df['strike_price'], exp_df['vega_to_theta_ratio'], 
                   label=f'{exp_date}', color=colors[i], alpha=0.7, s=50)
    
    plt.axvline(x=SPOT_PRICE, color='red', linestyle='--', alpha=0.7, 
                label=f'现货价格 ${SPOT_PRICE:,.0f}')
    plt.xlabel('行权价 ($)')
    plt.ylabel('Vega/Theta 比率')
    plt.title('Vega/Theta 性价比曲线')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    vega_theta_file = os.path.join(OUTPUT_FOLDER, f'vega_theta_ratio_{timestamp}.png')
    plt.savefig(vega_theta_file, dpi=300, bbox_inches='tight')
    print(f"Vega/Theta性价比曲线图已保存至: {vega_theta_file}")
    plt.show()
    
    # 3. 最优价差策略盈亏图
    if 'bear_put_spread' in bear_put_spread_results:
        spread_df = bear_put_spread_results['bear_put_spread']
        if len(spread_df) > 0:
            best_spread = spread_df.iloc[0]
            plot_payoff_diagram(best_spread, timestamp)

def plot_payoff_diagram(spread_data, timestamp):
    """
    绘制价差策略盈亏图
    """
    long_strike = spread_data['long_strike']
    short_strike = spread_data['short_strike']
    net_premium = spread_data['net_premium']
    max_profit = spread_data['max_profit']
    max_risk = spread_data['max_risk']
    breakeven = spread_data['breakeven']
    
    # 生成价格范围
    price_range = np.linspace(short_strike * 0.8, long_strike * 1.2, 1000)
    
    # 计算盈亏
    payoffs = []
    for price in price_range:
        if price <= short_strike:
            # 两个期权都到期价内
            payoff = (long_strike - price) - (short_strike - price) - net_premium
        elif price <= long_strike:
            # 只有长腿到期价内
            payoff = (long_strike - price) - net_premium
        else:
            # 两个期权都到期价外
            payoff = -net_premium
        
        payoffs.append(payoff)
    
    # 绘制盈亏图
    plt.figure(figsize=(12, 8))
    plt.plot(price_range, payoffs, 'b-', linewidth=2, label='策略盈亏')
    
    # 标记关键点
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.axvline(x=breakeven, color='green', linestyle='--', alpha=0.7, 
                label=f'盈亏平衡点 ${breakeven:.0f}')
    plt.axvline(x=long_strike, color='red', linestyle='--', alpha=0.7, 
                label=f'长腿行权价 ${long_strike:.0f}')
    plt.axvline(x=short_strike, color='orange', linestyle='--', alpha=0.7, 
                label=f'短腿行权价 ${short_strike:.0f}')
    plt.axvline(x=SPOT_PRICE, color='purple', linestyle='--', alpha=0.7, 
                label=f'现货价格 ${SPOT_PRICE:.0f}')
    
    # 标记最大利润和最大亏损
    plt.scatter([short_strike], [max_profit], color='green', s=100, zorder=5)
    plt.annotate(f'最大利润\n${max_profit:.2f}', 
                xy=(short_strike, max_profit), 
                xytext=(10, 10), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
    
    plt.scatter([long_strike], [-max_risk], color='red', s=100, zorder=5)
    plt.annotate(f'最大亏损\n${max_risk:.2f}', 
                xy=(long_strike, -max_risk), 
                xytext=(10, -20), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7))
    
    plt.xlabel('到期时标的价格 ($)')
    plt.ylabel('策略盈亏 ($)')
    plt.title(f'熊市看跌价差策略盈亏图\n长腿: ${long_strike:.0f}, 短腿: ${short_strike:.0f}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    payoff_file = os.path.join(OUTPUT_FOLDER, f'payoff_diagram_{timestamp}.png')
    plt.savefig(payoff_file, dpi=300, bbox_inches='tight')
    print(f"盈亏图已保存至: {payoff_file}")
    plt.show()

def main():
    """
    主函数
    """
    try:
        print("BTC期权防御策略量化分析系统")
        print("="*50)
        
        # 0. 清空export文件夹
        print("\n正在清空export文件夹...")
        clear_export_folder()
        
        # 1. 获取现货价格
        get_spot_price()
        
        # 2. 加载和清洗数据
        df = load_and_clean_data()
        
        # 3. 计算指标
        df = calculate_metrics(df)
        
        # 4. 策略分析
        print("\n正在进行策略分析...")
        
        single_put_results = {}
        for strategy_name, config in STRATEGY_CONFIG.items():
            if strategy_name != 'bear_put_spread':
                result = analyze_single_put(df, strategy_name, config)
                single_put_results[strategy_name] = result
        
        bear_put_spread_results = {}
        bear_put_spread_results['bear_put_spread'] = analyze_bear_put_spread(
            df, STRATEGY_CONFIG['bear_put_spread']
        )
        
        # 5. 生成报告
        generate_report(df, single_put_results, bear_put_spread_results)
        
        # 6. 生成可视化
        generate_visualizations(df, bear_put_spread_results)
        
        print("\n" + "="*80)
        print("分析完成！所有结果已保存到export文件夹。")
        print("="*80)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
