import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体，解决中文显示问题
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 初始条件
P0 = 2000            # 初始价格
eth0 = 5             # 初始ETH数量
usdc0 = 10000        # 初始USDC数量
k = eth0 * usdc0     # 常数乘积

# 价格区间（ETH价格）
prices = np.linspace(1000, 4000, 100)

# LP的资产价值
eth_lp = np.sqrt(k / prices)
usdc_lp = np.sqrt(k * prices)
lp_value = eth_lp * prices + usdc_lp

# 直接持币（HODL）价值
hodl_value = eth0 * prices + usdc0

# 无常损失（相对持币）
impermanent_loss = lp_value / hodl_value - 1

# 绘图
plt.figure(figsize=(10,6))
plt.plot(prices, hodl_value, label='持币价值 (HODL)', color='green')
plt.plot(prices, lp_value, label='做LP价值 (AMM)', color='red')
plt.title('持币 vs 做LP 收益曲线（ETH/USDC）')

plt.xlabel('ETH 价格 ($)')
plt.ylabel('资产总价值 ($)')
plt.legend(fontsize=13)
plt.grid(True, alpha=0.3)

# 添加初始条件说明
info_text = f'初始条件:\nETH初始价格: ${P0:.0f}\n初始ETH: {eth0:.1f}\n初始USDC: ${usdc0:.0f}\n总价值: ${eth0*P0 + usdc0:.0f}'
plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
         fontsize=14, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.show()

# 再画无常损失曲线
plt.figure(figsize=(10,5))
plt.plot(prices, impermanent_loss * 100, color='purple', linewidth=2)
plt.title('无常损失 (%) 随ETH价格变化')
plt.xlabel('ETH 价格 ($)')
plt.ylabel('相对持币的收益差 (%)')
plt.grid(True, alpha=0.3)
plt.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

# 添加初始条件说明
info_text = f'初始条件:\nETH初始价格: ${P0:.0f}\n初始ETH: {eth0:.1f}\n初始USDC: ${usdc0:.0f}'
plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
         fontsize=14, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 标记初始价格点
initial_loss = (np.sqrt(k / P0) * P0 + np.sqrt(k * P0)) / (eth0 * P0 + usdc0) - 1
plt.plot(P0, initial_loss * 100, 'ro', markersize=8, label=f'初始价格点 (${P0:.0f})')
plt.legend()

plt.show()
