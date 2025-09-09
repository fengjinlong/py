import os
import time
import pandas as pd
import pickle
import numpy as np
from glob import glob
from joblib import Parallel, delayed
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats
import seaborn as sns
sns.set(font = '',style='ticks',font_scale=1.4)
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm
import math

pd_display_rows  = 1000
pd_display_cols  = 100
pd_display_width = 1000
pd.set_option('display.max_rows', pd_display_rows)
pd.set_option('display.min_rows', pd_display_rows)
pd.set_option('display.max_columns', pd_display_cols)
pd.set_option('display.width', pd_display_width)
pd.set_option('display.max_colwidth', pd_display_width)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('expand_frame_repr', False)


data = pd.read_csv('BTC-USDT.csv', skiprows=1, encoding='gbk')
data['candle_begin_time'] = pd.to_datetime(data['candle_begin_time'])
data = data[['candle_begin_time','symbol','open','high','low','close']]


# print(data)

# 1.1 验算150d后的价格收益期望
def price_150d(data,day):
    data[str(day) + '_day_after_time'] = data['candle_begin_time'].shift(-24 * day)
    data[str(day) + 'close'] = data['close'].shift(-24 * day)
    for i in range(len(data) - 24 * day + 1):
        window_min = data['close'].iloc[i:i + 24 * day].min()
        data.at[i, 'min'] = window_min

    data1 = data[data['candle_begin_time'].dt.hour == 16]

    data1 = data1.dropna()
    data1 = data1.reset_index(drop=True)
    data1['-10%'] = data1['close']*0.9
    data1['-20%'] = data1['close'] * 0.8
    data1['-30%'] = data1['close'] * 0.7
    data1['-40%'] = data1['close'] * 0.6
    data1['-50%'] = data1['close'] * 0.5

    # print(data1)

    data1['diff-10'] = np.where(data1['-10%'] >= data1['150close'], data1['-10%'] - data1['150close'], 0)
    data1['diff-20'] = np.where(data1['-20%'] >= data1['150close'], data1['-20%'] - data1['150close'], 0)
    data1['diff-30'] = np.where(data1['-30%'] >= data1['150close'], data1['-30%'] - data1['150close'], 0)
    data1['diff-40'] = np.where(data1['-40%'] >= data1['150close'], data1['-40%'] - data1['150close'], 0)
    data1['diff-50'] = np.where(data1['-50%'] >= data1['150close'], data1['-50%'] - data1['150close'], 0)

    data1['cost-10'] = 0.0581 * data1['close']
    data1['cost-20'] = 0.0268 * data1['close']
    data1['cost-30'] = 0.0130 * data1['close']
    data1['cost-40'] = 0.0058 * data1['close']
    data1['cost-50'] = 0.0030 * data1['close']
    # print(data1)

    cost10 = data1['cost-10'].sum()
    income10 = data1['diff-10'].sum()
    print('-10%',cost10,income10,income10/cost10)

    cost20 = data1['cost-20'].sum()
    income20 = data1['diff-20'].sum()
    print('-20%',cost20, income20,income20/cost20)

    cost30 = data1['cost-30'].sum()
    income30 = data1['diff-30'].sum()
    print('-30%',cost30, income30,income30/cost30)

    cost40 = data1['cost-40'].sum()
    income40 = data1['diff-40'].sum()
    print('-40%', cost40, income40, income40 / cost40)

    cost50 = data1['cost-50'].sum()
    income50 = data1['diff-50'].sum()
    print('-50%', cost50, income50, income50 / cost50)

    return data1

data1 = price_150d(data,150)

# exit()
def effect_ratio(data1):
    data1['effect'] = np.where(data1['-10%'] > data1['min'] * 1.05, 1, 0)
    effect_ratio10 = data1['effect'].sum() / len(data1)
    print(data1['effect'].sum() , len(data1))
    print('-10%',effect_ratio10)

    data1['effect'] = np.where(data1['-20%'] > data1['min'] * 1.05, 1, 0)
    effect_ratio20 = data1['effect'].sum() / len(data1)
    print(data1['effect'].sum(), len(data1))
    print('-20%', effect_ratio20)

    data1['effect'] = np.where(data1['-30%'] > data1['min'] * 1.05, 1, 0)
    effect_ratio30 = data1['effect'].sum() / len(data1)
    print(data1['effect'].sum(), len(data1))
    print('-30%', effect_ratio30)

    data1['effect'] = np.where(data1['-40%'] > data1['min'] * 1.05, 1, 0)
    effect_ratio40 = data1['effect'].sum() / len(data1)
    print(data1['effect'].sum(), len(data1))
    print('-40%', effect_ratio40)

    data1['effect'] = np.where(data1['-50%'] > data1['min'] * 1.05, 1, 0)
    effect_ratio50 = data1['effect'].sum() / len(data1)
    print(data1['effect'].sum(), len(data1))
    print('-50%', effect_ratio50)



effect_ratio(data1)


def huatu(time,close,diff):
    time = pd.to_datetime(time)

    # 创建图形和主轴
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 画主轴：close 曲线
    color1 = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Close Price', color=color1)
    ax1.plot(time, close, color=color1, label='Close')
    ax1.tick_params(axis='y', labelcolor=color1)

    # 创建次坐标轴，共享x轴
    ax2 = ax1.twinx()

    # 画次轴：diff 曲线
    color2 = 'tab:red'
    ax2.set_ylabel('Diff', color=color2)
    ax2.plot(time, diff, color=color2, linestyle='--', label='Diff')
    ax2.tick_params(axis='y', labelcolor=color2)

    # 添加图例
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    # 美化时间坐标轴
    fig.autofmt_xdate()

    # 显示图形
    plt.title('Close and Diff Over Time')
    plt.tight_layout()
    plt.savefig('figure.png', dpi=200, bbox_inches='tight')
    plt.close(fig)




huatu(data1['candle_begin_time'],data1['close'],data1['diff-10'])
# huatu(data1['candle_begin_time'],data1['close'],data1['diff-30'])
# huatu(data1['candle_begin_time'],data1['close'],data1['diff-50'])


exit()
