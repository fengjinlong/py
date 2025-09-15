# qsy_sp_jm.py 水印去除优化方案

## 原始文件特点
- 处理 **2个水印区域**：
  - WATERMARK1: 坐标(995, 610) 大小(218x78) - 右下角大水印
  - WATERMARK2: 坐标(10, 10) 大小(80x42) - 左上角小水印
- 使用简单高斯模糊 `(51, 51)`
- 无水印调试框功能

## 优化改进

### 1. 增强功能
- ✅ 添加调试框功能 (`DRAW_WATERMARK_BOX`)
- ✅ 多种水印去除方法选择
- ✅ 边界检查防止越界
- ✅ 详细的状态输出

### 2. 水印去除方法

#### 基础优化版本 (qsy_sp_jm_optimized.py)
- **enhanced_blur**: 多重模糊 + 中值滤波 + 双边滤波
- **gaussian_blur**: 强化高斯模糊 (101x101)
- **inpainting**: 图像修复技术
- **morphology**: 形态学操作

#### 超级增强版本 (qsy_sp_jm_advanced.py)
- **super_enhanced**: 5步处理流程
  1. 极强高斯模糊 (201→151→101)
  2. 双重中值模糊 (21→15)
  3. 双边滤波平滑
  4. 形态学开运算
  5. 最终高斯模糊

## 使用方法

### 方法一：使用优化版本
```bash
python qsy_sp_jm_optimized.py
```

### 方法二：使用超级增强版本（推荐）
```bash
python qsy_sp_jm_advanced.py
```

### 方法三：修改原文件
将原文件的 `remove_watermark` 函数替换为优化版本。

## 参数配置

### 调试模式
```python
DRAW_WATERMARK_BOX = True  # 显示红色框确认水印位置
```

### 选择去除方法（默认：morphology）
```python
REMOVAL_METHOD = "morphology"  # 推荐用于顽固水印
```

### 调整水印区域
```python
WATERMARK_AREAS = [
    {"x": 995, "y": 610, "w": 218, "h": 78, "label": "WATERMARK1"},
    {"x": 10, "y": 10, "w": 80, "h": 42, "label": "WATERMARK2"},
    # 添加更多水印区域
]
```

## 效果对比

| 方法 | 处理速度 | 效果质量 | 适用场景 |
|------|----------|----------|----------|
| gaussian_blur | 快 | 一般 | 简单水印 |
| enhanced_blur | 中等 | 好 | 一般水印 |
| super_enhanced | 慢 | 很好 | 顽固水印 |
| inpainting | 中等 | 好 | 复杂水印 |
| morphology | 快 | 中等 | 特定水印 |

## 特别说明

### 针对两个水印区域
1. **右下角大水印** (218x78): 建议使用 `super_enhanced` 方法
2. **左上角小水印** (80x42): 可以使用 `enhanced_blur` 方法

### 性能优化建议
- 如果两个水印效果要求不同，可以分别设置不同的处理方法
- 建议先用调试模式确认水印位置是否准确
- 处理大视频时，超级增强方法可能需要较长时间

## 文件结构
```
qsy/
├── qsy_sp_jm.py                    # 原始文件
├── qsy_sp_jm_optimized.py         # 基础优化版本
├── qsy_sp_jm_advanced.py          # 超级增强版本
└── qsy_sp_jm_优化说明.md          # 本说明文档
```

## 使用建议

1. **首次使用**：开启 `DRAW_WATERMARK_BOX = True` 确认水印位置
2. **测试阶段**：使用 `super_enhanced` 方法获得最佳效果
3. **批量处理**：确认效果满意后关闭调试模式
4. **性能考虑**：如果效果满意但速度慢，可以尝试 `enhanced_blur`

现在您的水印去除效果应该会显著改善，特别是对于右下角的大水印区域！
