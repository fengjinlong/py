import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np
from matplotlib.patches import FancyArrowPatch
import os

# 读取 CSV
# file_name = "ETH-26DEC25-export.csv"  # 替换成你的文件名
file_name = "BTC-26DEC25-export.csv"  # 替换成你的文件名
df = pd.read_csv(file_name)

# 从文件名提取基础名称（去掉扩展名）
base_name = os.path.splitext(file_name)[0]

# 创建 export 文件夹（如果不存在）
export_dir = "export"
os.makedirs(export_dir, exist_ok=True)

# 1. 只保留看涨期权（C 结尾）
df = df[df["产品"].str.endswith("-C")].copy()

# 2. 从 "产品" 字段解析出行权价
# 格式类似：ETH-26DEC25-1200-C
df["Strike"] = df["产品"].apply(lambda x: int(re.findall(r"-(\d+)-C$", x)[0]))

# 3. 转换关键列为数值型（避免有 "-" 字符）
# 使用 Δ|增量 列作为 Delta 值
for col in ["Δ|增量", "Theta", "Gamma"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 去掉缺失值
df = df.dropna(subset=["Δ|增量", "Theta"])

# 添加Theta过滤条件：剔除Theta绝对值太小的点
df = df[df["Theta"].abs() >= 1e-3].copy()

# 4. 计算性价比指标
df["Delta/Theta"] = df["Δ|增量"] / df["Theta"].abs()
df["Gamma/Theta"] = df["Gamma"] / df["Theta"].abs()

# 5. 初始化推荐列
df["Recommendation"] = "Normal"

# 6. 定义OTM筛选条件：Delta范围筛选
delta_min = 0.15 # 最小Delta值
delta_max = 0.45   # 最大Delta值
otm_condition = (df["Δ|增量"].abs() >= delta_min) & (df["Δ|增量"].abs() <= delta_max)

print(f"OTM筛选条件: {delta_min} ≤ |Delta| ≤ {delta_max}")
print(f"符合OTM条件的合约数量: {otm_condition.sum()}")
print(f"不符合OTM条件的合约数量: {(~otm_condition).sum()}")

# 标记前 3 名 (Delta/Theta) - 仅在OTM范围内筛选
otm_df = df[otm_condition].copy()
if len(otm_df) >= 3:
    top3_delta = otm_df["Delta/Theta"].nlargest(3).index
    for rank, idx in enumerate(top3_delta, start=1):
        df.loc[idx, "Recommendation"] = f"Top{rank} (Delta/Theta)"
    print(f"\n前3名Delta/Theta (OTM范围): {len(top3_delta)}个")
else:
    top3_delta = []
    print(f"\n警告: OTM范围内合约数量不足3个 ({len(otm_df)}个)")

# 标记前 3 名 (Gamma/Theta) - 不限制OTM条件
top3_gamma = df["Gamma/Theta"].nlargest(3).index
for rank, idx in enumerate(top3_gamma, start=1):
    if df.loc[idx, "Recommendation"] == "Normal":
        df.loc[idx, "Recommendation"] = f"Top{rank} (Gamma/Theta)"
    else:
        df.loc[idx, "Recommendation"] += f" + Top{rank} (Gamma/Theta)"

# 7. 打印推荐结果
if len(top3_delta) > 0:
    print("\n前 3 名 Delta/Theta 行权价 (OTM范围):")
    print(df.loc[top3_delta, ["产品", "Strike", "Δ|增量", "Delta/Theta"]])
else:
    print("\n前 3 名 Delta/Theta 行权价 (OTM范围): 无符合条件的数据")

print("\n前 3 名 Gamma/Theta 行权价:")
print(df.loc[top3_gamma, ["产品", "Strike", "Gamma", "Gamma/Theta"]])

print("\n完整数据表：")
print(df[["产品", "Strike", "Δ|增量", "Gamma", "Theta", 
          "Delta/Theta", "Gamma/Theta", "Recommendation"]])

# 8. 画图
plt.figure(figsize=(16, 7))

# Δ/|Θ| 曲线 - 使用对数坐标
plt.subplot(1, 2, 1)
plt.plot(df["Strike"], df["Delta/Theta"], marker="o", alpha=0.7, label="All")
plt.plot(otm_df["Strike"], otm_df["Delta/Theta"], marker="o", color="blue", 
         linewidth=2, label="OTM Range", alpha=0.9)

if len(top3_delta) > 0:
    plt.scatter(df.loc[top3_delta, "Strike"], df.loc[top3_delta, "Delta/Theta"],
                color="green", s=80, label="Top3 Delta/Theta", zorder=5, alpha=0.8)
    
    # 使用箭头指引，将标签放在空白区域
    top3_delta_sorted = df.loc[top3_delta].sort_values("Strike")
    for i, (idx, row) in enumerate(top3_delta_sorted.iterrows()):
        # 计算标签位置 - 放在空白区域
        strike = row["Strike"]
        value = row["Delta/Theta"]
        
        # 根据位置选择标签位置
        if i == 0:  # 第一个点 - 放在左上方
            label_x = strike - 200
            label_y = value * 4
            arrow_start = (strike - 50, value * 1.1)
        elif i == 1:  # 第二个点 - 放在右上方
            label_x = strike + 200
            label_y = value * 8
            arrow_start = (strike + 50, value * 1.1)
        else:  # 第三个点 - 放在右下方
            label_x = strike + 200
            label_y = value * 16
            arrow_start = (strike + 50, value * 0.9)
        
        # 添加箭头
        arrow = FancyArrowPatch((arrow_start[0], arrow_start[1]), 
                               (label_x, label_y),
                               arrowstyle='->', mutation_scale=15, 
                               color='green', linewidth=2, alpha=0.8)
        plt.gca().add_patch(arrow)
        
        # 添加标签
        plt.text(label_x, label_y, str(int(strike)), 
                 fontsize=10, ha="center", va="center",
                 color="green", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white", 
                          edgecolor="green", alpha=0.9, linewidth=2))

# 添加OTM范围标记线
plt.axhline(y=df[otm_condition]["Delta/Theta"].max(), color="red", linestyle="--", alpha=0.5, label="OTM Max")
plt.axhline(y=df[otm_condition]["Delta/Theta"].min(), color="red", linestyle="--", alpha=0.5, label="OTM Min")

plt.title("Delta/Theta vs Strike (Log Scale)\nOTM Range Highlighted", fontsize=12)
plt.xlabel("Strike Price", fontsize=11)
plt.ylabel("Delta/|Theta| (Log Scale)", fontsize=11)
plt.yscale('log')  # 使用对数坐标
plt.legend()
plt.grid(True, alpha=0.3)

# Γ/|Θ| 曲线
plt.subplot(1, 2, 2)
plt.plot(df["Strike"], df["Gamma/Theta"], marker="o")
plt.scatter(df.loc[top3_gamma, "Strike"], df.loc[top3_gamma, "Gamma/Theta"],
            color="green", s=80, label="Top3", zorder=5, alpha=0.8)

# 使用箭头指引，将标签放在空白区域
top3_gamma_sorted = df.loc[top3_gamma].sort_values("Strike")
for i, (idx, row) in enumerate(top3_gamma_sorted.iterrows()):
    # 计算标签位置 - 放在空白区域
    strike = row["Strike"]
    value = row["Gamma/Theta"]
    
    # 根据位置选择标签位置
    if i == 0:  # 第一个点 - 放在左上方
        label_x = strike - 300
        label_y = value * 1.2
        arrow_start = (strike - 100, value * 1.05)
    elif i == 1:  # 第二个点 - 放在右上方
        label_x = strike + 300
        label_y = value * 1.2
        arrow_start = (strike + 100, value * 1.05)
    else:  # 第三个点 - 放在右下方
        label_x = strike + 300
        label_y = value * 0.8
        arrow_start = (strike + 100, value * 0.95)
    
    # 添加箭头
    arrow = FancyArrowPatch((arrow_start[0], arrow_start[1]), 
                           (label_x, label_y),
                           arrowstyle='->', mutation_scale=15, 
                           color='green', linewidth=2, alpha=0.8)
    plt.gca().add_patch(arrow)
    
    # 添加标签
    plt.text(label_x, label_y, str(int(strike)), 
             fontsize=10, ha="center", va="center",
             color="green", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", 
                      edgecolor="green", alpha=0.9, linewidth=2))

plt.title("Gamma/Theta vs Strike", fontsize=12)
plt.xlabel("Strike Price", fontsize=11)
plt.ylabel("Gamma/|Theta|", fontsize=11)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()

# 根据输入文件名生成输出文件名，保存到 export 文件夹
image_file = os.path.join(export_dir, f"{base_name}_options_analysis.png")
plt.savefig(image_file, dpi=300, bbox_inches='tight')
print(f"\n图片已保存为: {image_file}")

plt.show()

# 9. 创建带不同颜色标记的Excel文件
output_file = os.path.join(export_dir, f"{base_name}_options_with_recommendation.xlsx")
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # 写入数据
    df.to_excel(writer, sheet_name='期权分析', index=False)
    
    # 获取工作表
    worksheet = writer.sheets['期权分析']
    
    # 导入样式
    from openpyxl.styles import PatternFill, Font, Border, Side
    
    # 定义不同颜色背景
    delta_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")  # 浅绿色 - Delta/Theta
    gamma_fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")  # 天蓝色 - Gamma/Theta
    both_fill = PatternFill(start_color="DDA0DD", end_color="DDA0DD", fill_type="solid")   # 紫色 - 两者都有
    bold_font = Font(bold=True)
    
    # 定义边框
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 为前3名Delta/Theta添加浅绿色背景
    for idx in top3_delta:
        row_num = df.index.get_loc(idx) + 2  # +2 因为Excel从1开始，还有标题行
        for col_num in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=row_num, column=col_num)
            cell.fill = delta_fill
            cell.font = bold_font
            cell.border = thin_border
    
    # 为前3名Gamma/Theta添加天蓝色背景
    for idx in top3_gamma:
        row_num = df.index.get_loc(idx) + 2  # +2 因为Excel从1开始，还有标题行
        for col_num in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=row_num, column=col_num)
            # 检查是否已经有Delta/Theta标记
            if "Delta/Theta" in df.loc[idx, "Recommendation"]:
                cell.fill = both_fill  # 紫色 - 两者都有
            else:
                cell.fill = gamma_fill  # 天蓝色 - 只有Gamma/Theta
            cell.font = bold_font
            cell.border = thin_border
    
    # 为所有单元格添加边框
    for row in range(1, len(df) + 2):  # +2 因为包含标题行
        for col in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=row, column=col)
            if not cell.border.left:  # 如果还没有边框
                cell.border = thin_border

# 10. 创建增强版CSV文件（添加颜色标记说明）
csv_file = os.path.join(export_dir, f"{base_name}_options_with_recommendation.csv")

# 创建带颜色标记的CSV数据
csv_df = df.copy()

# 添加颜色标记列
def get_color_mark(recommendation):
    if "Delta/Theta" in recommendation and "Gamma/Theta" in recommendation:
        return "🟣 紫色标记 (Delta+Gamma双优)"
    elif "Delta/Theta" in recommendation:
        return "🟢 绿色标记 (Delta/Theta优)"
    elif "Gamma/Theta" in recommendation:
        return "🔵 蓝色标记 (Gamma/Theta优)"
    else:
        return "⚪ 普通"

csv_df["颜色标记"] = csv_df["Recommendation"].apply(get_color_mark)

# 重新排列列，把颜色标记放在前面
cols = ["颜色标记", "产品", "Strike", "Δ|增量", "Gamma", "Theta", 
        "Delta/Theta", "Gamma/Theta", "Recommendation"]
csv_df = csv_df[cols]

# 保存CSV
csv_df.to_csv(csv_file, index=False, encoding='utf-8-sig')

print(f"\n结果已写入 {output_file} (带颜色标记)")
print(f"结果已写入 {csv_file} (带颜色说明)")

# 打印过滤后的数据统计
print(f"\n过滤前数据点数量: {len(pd.read_csv(file_name)[pd.read_csv(file_name)['产品'].str.endswith('-C')])}")
print(f"过滤后数据点数量: {len(df)}")
print(f"Theta过滤条件: |Theta| >= 1e-3")
print(f"OTM筛选条件: {delta_min} ≤ |Delta| ≤ {delta_max}")
print(f"符合OTM条件的合约: {otm_condition.sum()}个")

# 打印颜色标记说明
print(f"\n=== 颜色标记说明 ===")
print(f"🟢 绿色标记: Top3 Delta/Theta (OTM范围内)")
print(f"🔵 蓝色标记: Top3 Gamma/Theta (全范围)")
print(f"🟣 紫色标记: 同时获得Delta/Theta和Gamma/Theta推荐")
print(f"⚪ 普通标记: 未获得推荐")

# 打印文件命名信息
print(f"\n=== 文件命名规则 ===")
print(f"输入文件: {file_name}")
print(f"输出图片: {image_file}")
print(f"输出Excel: {output_file}")
print(f"输出CSV: {csv_file}")
print(f"基础名称: {base_name}")
print(f"输出目录: {export_dir}")
