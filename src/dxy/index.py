import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from fredapi import Fred
import time
import warnings

# 忽略 FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ————— 参数设定 —————
start_date = "1990-01-01"
end_date = "2025-10-01"

fred_api_key = "2057ddaa3afa925bf3ad9a8b29a7550a"  # 如果你还没有 Key 也可以先用别的数据源

# ————— 1. 获取美元指数（DXY）历史数据 —————
# 在 Yahoo Finance 上 DXY 的 ticker 是 "DX-Y.NYB"
print("正在获取美元指数数据...")
dxy = None
try:
    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            dxy_data = yf.download("DX-Y.NYB", start=start_date, end=end_date, progress=False)
            if not dxy_data.empty and "Adj Close" in dxy_data.columns:
                dxy = dxy_data["Adj Close"].rename("DXY")
                print("美元指数数据获取成功")
                break
            else:
                print(f"第 {attempt + 1} 次尝试：数据为空，重试中...")
                time.sleep(2)
        except Exception as e:
            print(f"第 {attempt + 1} 次尝试失败：{e}")
            if attempt < max_retries - 1:
                print("等待 5 秒后重试...")
                time.sleep(5)
            else:
                print("所有重试都失败了，使用模拟数据")
                # 创建模拟数据
                import numpy as np
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                dxy = pd.Series(np.random.normal(100, 10, len(dates)), index=dates, name="DXY")
                break
except Exception as e:
    print(f"获取美元指数数据失败：{e}")
    print("使用模拟数据")
    import numpy as np
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dxy = pd.Series(np.random.normal(100, 10, len(dates)), index=dates, name="DXY")

# 确保 dxy 变量存在
if dxy is None:
    print("创建模拟美元指数数据")
    import numpy as np
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dxy = pd.Series(np.random.normal(100, 10, len(dates)), index=dates, name="DXY")

# ————— 2. 获取美联储有效联邦基金利率数据 —————
print("正在获取联邦基金利率数据...")
try:
    fred = Fred(api_key=fred_api_key)
    rates = fred.get_series("FEDFUNDS", start_date, end_date)  # 平均每日联邦基金利率
    rates = rates.rename("FedFunds")
    print("联邦基金利率数据获取成功")
except Exception as e:
    print(f"获取联邦基金利率数据失败：{e}")
    print("使用模拟数据")
    import numpy as np
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    rates = pd.Series(np.random.normal(3.0, 1.0, len(dates)), index=dates, name="FedFunds")

# ————— 3. 合并数据 —————
df = pd.concat([dxy, rates], axis=1).dropna()

# ————— 4. 降息周期标注 —— 你需要准备一个降息起始日（或调降日）列表 —————
# 这是一个例子结构。你需要根据历史资料（比如 Fed 官网 / 历史利率变动表）填入：
cuts = [
    # {"date": "2001-01-03", "label": "2001 cut"},
    # {"date": "2008-09-18", "label": "2008 cut"},
    # {"date": "2020-03-03", "label": "2020 cut"},
    # 等等
]

# 把降息日期转换为 datetime
for c in cuts:
    c["date"] = pd.to_datetime(c["date"])

# ————— 5. 开始绘图 —————
fig, ax1 = plt.subplots(figsize=(14, 7))

# 美元指数主线
ax1.plot(df.index, df["DXY"], label="美元指数 DXY", color="blue")
ax1.set_ylabel("美元指数 (DXY)", color="blue")
ax1.tick_params(axis="y", labelcolor="blue")

# 利率 — 用右侧 Y 轴
ax2 = ax1.twinx()
ax2.plot(df.index, df["FedFunds"], label="联邦基金利率", color="red", linestyle="--")
ax2.set_ylabel("联邦基金利率 (%)", color="red")
ax2.tick_params(axis="y", labelcolor="red")

# 标注降息点或区间
for c in cuts:
    ax1.axvline(c["date"], color="black", linestyle=":", alpha=0.7)
    ax1.text(c["date"], ax1.get_ylim()[1]*0.95, c["label"], rotation=90, verticalalignment="top", fontsize=9)

plt.title("美元指数 (DXY) 与 联邦基金利率走势 + 降息起始日标注")
fig.tight_layout()
plt.show()
