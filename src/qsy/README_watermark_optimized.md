# 多水印区域去除工具 - 优化版

## 功能特性

### 🎯 核心功能
- **多水印区域支持**: 可同时处理多个水印区域
- **配置文件管理**: 通过 JSON 配置文件管理水印区域
- **智能坐标验证**: 自动调整坐标以适应不同尺寸的图片
- **灵活的区域控制**: 可单独启用/禁用每个水印区域
- **详细日志记录**: 完整的处理过程日志

### 🔧 技术优化
- **面向对象设计**: 使用类封装，代码结构清晰
- **类型提示**: 完整的类型注解，提高代码可读性
- **异常处理**: 完善的错误处理机制
- **性能优化**: 组合掩码技术，一次处理所有水印区域

## 使用方法

### 1. 基本使用
```bash
python qsy_tp_jm_optimized.py
```

### 2. 配置水印区域
编辑 `watermark_config.json` 文件：

```json
{
  "watermark_regions": [
    {
      "name": "右下角水印",
      "coordinates": [2648, 1360, 2766, 1480],
      "enabled": true
    },
    {
      "name": "左上角水印", 
      "coordinates": [100, 100, 300, 200],
      "enabled": true
    }
  ]
}
```

### 3. 编程接口使用
```python
from qsy_tp_jm_optimized import WatermarkRemover

# 创建去除器
remover = WatermarkRemover('input_images/', 'output_images/')

# 添加新的水印区域
remover.add_watermark_region("新水印", [500, 500, 600, 600])

# 处理所有图片
results = remover.process_all_images()
print(f"成功处理: {results['success']} 张")
```

## 配置说明

### 水印区域配置
- `name`: 水印区域名称（用于日志识别）
- `coordinates`: 坐标数组 `[x1, y1, x2, y2]`
  - `x1, y1`: 左上角坐标
  - `x2, y2`: 右下角坐标
- `enabled`: 是否启用该区域（true/false）

### 坐标系统
- 原点 (0,0) 位于图片左上角
- X 轴向右递增，Y 轴向下递增
- 坐标会自动调整以适应图片实际尺寸

## 高级功能

### 1. 动态添加水印区域
```python
remover = WatermarkRemover()
remover.add_watermark_region("动态水印", [100, 100, 200, 200])
```

### 2. 自定义修复参数
```python
# 使用不同的修复算法
result = remover.remove_watermarks(img, 
                                 inpaint_method=cv2.INPAINT_NS,
                                 inpaint_radius=5)
```

### 3. 批量处理特定文件
```python
# 处理特定文件
img_path = Path('input_images/specific_image.jpg')
success = remover.process_single_image(img_path)
```

## 支持的图片格式
- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)

## 日志输出示例
```
2024-01-01 10:00:00 - INFO - 找到 5 个图片文件
2024-01-01 10:00:01 - INFO - 开始处理: image1.jpg (尺寸: (1920, 1080, 3))
2024-01-01 10:00:01 - INFO - 添加水印区域: 右下角水印 - (2648,1360,2766,1480)
2024-01-01 10:00:01 - INFO - 处理了 12544 个水印像素
2024-01-01 10:00:02 - INFO - 成功保存: output_images/image1.jpg
```

## 性能优化建议

1. **合理设置水印区域**: 只标记真正的水印区域，避免过度处理
2. **批量处理**: 一次性处理多张图片比单张处理更高效
3. **坐标优化**: 使用精确的坐标减少不必要的像素处理
4. **内存管理**: 处理大图片时注意内存使用

## 故障排除

### 常见问题
1. **坐标超出图片范围**: 系统会自动调整坐标
2. **配置文件格式错误**: 检查 JSON 语法是否正确
3. **图片无法读取**: 确认图片格式是否支持
4. **处理效果不佳**: 尝试调整修复半径或使用不同算法

### 调试模式
设置日志级别为 DEBUG 获取更详细的信息：
```python
logging.basicConfig(level=logging.DEBUG)
```
