# 多点水印去除脚本使用说明

## 功能特点

- ✅ 支持处理多个水印区域
- ✅ 配置文件管理，方便调整水印位置
- ✅ 支持启用/禁用特定水印点
- ✅ 自动坐标边界检查
- ✅ 详细的处理日志输出

## 文件说明

- `qsy_tp_jm_shorts_multi.py` - 优化后的多点水印处理脚本
- `watermark_config.json` - 水印配置文件
- `input_images/` - 输入图片文件夹
- `output_images/` - 输出图片文件夹

## 使用方法

### 1. 基本使用
```bash
python qsy_tp_jm_shorts_multi.py
```

### 2. 配置水印区域

编辑 `watermark_config.json` 文件：

```json
{
  "description": "水印区域配置文件",
  "watermarks": [
    {
      "name": "右下角水印1",
      "coordinates": [2648, 1360, 2766, 1480],
      "enabled": true
    },
    {
      "name": "水印点2",
      "coordinates": [17, 21, 177, 82],
      "enabled": true
    }
  ]
}
```

### 3. 配置参数说明

- `name`: 水印区域名称（用于日志显示）
- `coordinates`: 水印区域坐标 [x1, y1, x2, y2]
  - x1, y1: 左上角坐标
  - x2, y2: 右下角坐标
- `enabled`: 是否启用该水印区域（true/false）

### 4. 添加新的水印点

在 `watermark_config.json` 中添加新的水印配置：

```json
{
  "name": "新水印点",
  "coordinates": [x1, y1, x2, y2],
  "enabled": true
}
```

### 5. 临时禁用水印点

将对应水印的 `enabled` 设置为 `false`：

```json
{
  "name": "水印点2",
  "coordinates": [17, 21, 177, 82],
  "enabled": false
}
```

## 优化改进

相比原版本，新版本具有以下优势：

1. **多点支持**: 可以同时处理多个水印区域
2. **配置管理**: 通过JSON文件管理水印配置，无需修改代码
3. **灵活控制**: 可以单独启用/禁用每个水印点
4. **错误处理**: 增加了坐标验证和错误处理
5. **详细日志**: 提供详细的处理过程日志
6. **自动适配**: 自动调整坐标以适应不同尺寸的图片

## 注意事项

- 确保 `input_images/` 文件夹中有要处理的图片
- 坐标格式为 [x1, y1, x2, y2]，其中 x1 < x2, y1 < y2
- 脚本会自动检查坐标边界，确保不超出图片范围
- 处理后的图片会保存到 `output_images/` 文件夹
