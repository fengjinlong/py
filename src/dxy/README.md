# 美元指数与联邦基金利率分析

这个脚本用于分析美元指数（DXY）与联邦基金利率的历史走势关系。

## 功能特点

- 获取美元指数（DXY）历史数据
- 获取联邦基金利率数据
- 绘制双轴图表显示两者关系
- 支持降息周期标注
- 自动处理API限制和错误

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python3 index.py
```

## 数据源

- **美元指数**: Yahoo Finance (DX-Y.NYB)
- **联邦基金利率**: FRED API (FEDFUNDS)

## 注意事项

- 需要有效的FRED API密钥
- 如果Yahoo Finance API被限制，程序会自动使用模拟数据
- 图表支持中文显示

## 自定义

您可以在代码中修改以下参数：
- `start_date` 和 `end_date`: 数据时间范围
- `fred_api_key`: FRED API密钥
- `cuts`: 降息周期标注列表
