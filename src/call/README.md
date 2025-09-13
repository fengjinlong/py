# 期权分析工具 - 优化版

## 功能说明

这是一个用于分析期权数据的Python工具，能够：

1. **自动处理多个CSV文件** - 批量分析data目录下的所有期权数据文件
2. **智能筛选** - 基于Delta、Theta、Gamma、Vega等希腊字母进行筛选
3. **可视化分析** - 生成专业的图表展示分析结果
4. **多格式输出** - 支持Excel、CSV、PNG等多种输出格式
5. **颜色标记** - 用不同颜色标记不同类型的推荐
6. **文件标识** - 每个生成的图片都包含文件名和生成时间信息

## 文件结构

```
src/call/
├── yqcallxjb.py          # 主程序文件
├── run_analysis.sh       # 运行脚本
├── README.md             # 说明文档
├── data/                 # 数据文件夹
│   ├── ETH-26DEC25-export.csv
│   ├── BTC-26DEC25-export.csv
│   └── ...
└── export/               # 输出文件夹（自动创建）
    ├── *_options_analysis.png
    ├── *_options_with_recommendation.xlsx
    └── *_options_with_recommendation.csv
```

## 使用方法

### 方法1：使用运行脚本（推荐）

```bash
cd src/call
./run_analysis.sh
```

### 方法2：直接运行Python

```bash
cd src/call
python3 yqcallxjb.py
```

## 数据准备

1. 将CSV数据文件放入 `data/` 文件夹
2. CSV文件应包含以下列：
   - `产品` - 期权产品名称（如：ETH-26DEC25-1200-C）
   - `Δ|增量` - Delta值
   - `Theta` - Theta值
   - `Gamma` - Gamma值
   - `Vega` - Vega值

## 输出说明

### 图表文件
- `*_options_analysis.png` - 包含三个子图的分析图表
  - **图表顶部显示文件名** - 如"期权分析报告 - ETH-26DEC25-export"
  - **右上角显示文件信息** - 包含数据文件名和生成时间
  - Delta/Theta vs Strike（对数坐标）
  - Gamma/Theta vs Strike
  - Vega/Theta vs Strike（OTM范围高亮）

### Excel文件
- `*_options_with_recommendation.xlsx` - 带颜色标记的详细数据表

### CSV文件
- `*_options_with_recommendation.csv` - 带颜色标记说明的CSV文件

## 颜色标记说明

- 🟢 **绿色标记**: Top3 Delta/Theta（OTM范围内）
- 🔵 **蓝色标记**: Top3 Gamma/Theta（全范围）
- 🩷 **粉色标记**: Top3 Vega/Theta（OTM范围内）
- 🟣 **紫色标记**: 同时获得两种推荐
- 🟡 **金色标记**: 同时获得三种推荐
- ⚪ **普通标记**: 未获得推荐

## 筛选条件

- **OTM筛选**: 0.15 ≤ |Delta| ≤ 0.45
- **Theta过滤**: |Theta| >= 1e-3
- **期权类型**: 仅分析看涨期权（-C结尾）

## 图表特性

### 新增功能
- **文件标识**: 每个图表顶部显示对应的CSV文件名
- **时间戳**: 图表右上角显示生成时间
- **统计信息**: 左下角显示OTM合约数量和推荐数量
- **优化布局**: 图表尺寸调整为24x10，提供更好的显示效果

### 图表内容
1. **Delta/Theta图**: 使用对数坐标，突出显示OTM范围
2. **Gamma/Theta图**: 显示所有合约的Gamma/Theta比值
3. **Vega/Theta图**: 重点突出OTM范围内的Vega/Theta比值

## 依赖包

```bash
```

## 注意事项

1. 确保CSV文件格式正确，包含必要的列
2. 程序会自动创建export文件夹存放输出文件
3. 如果某个文件处理失败，程序会继续处理其他文件
4. 建议在运行前备份重要数据
5. 生成的图片包含文件名标识，便于区分不同数据源的分析结果

## 故障排除

### 常见问题

1. **找不到CSV文件**
   - 检查data文件夹是否存在
   - 确认CSV文件在data文件夹中

2. **缺少依赖包**

3. **图表显示问题**
   - 确保系统支持中文字体显示
   - 在macOS上可能需要安装中文字体

4. **Excel文件无法打开**
   - 确保安装了openpyxl包
   - 检查文件是否被其他程序占用

5. **图片标题显示异常**
   - 确保文件名不包含特殊字符
   - 检查matplotlib字体设置

## 更新日志

- v2.1: 添加文件标识功能，图表显示文件名和生成时间
- v2.0: 优化版，支持批量处理，改进图表显示
- v1.0: 基础版本，单文件处理
