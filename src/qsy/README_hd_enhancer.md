# QSY 图片高清化工具

这是一个专门用于图片高清化处理的Python工具，结合了多种先进的图像处理算法，能够显著提升图片的清晰度和质量。

## 功能特点

### 1. 多种放大算法
- **双三次插值 (Bicubic)**: 经典的图像放大算法，平衡速度和质量
- **Lanczos插值**: 高质量的图像放大算法，细节保持更好
- **ESRGAN模拟**: 模拟ESRGAN深度学习算法的效果，通过锐化增强细节

### 2. 多种增强模式
- **基础增强**: 仅进行锐化处理
- **高级增强**: 锐化 + 对比度 + 色彩饱和度 + 亮度调整
- **超级增强**: 高级增强 + 双边滤波 + 去噪 + 拉普拉斯锐化

### 3. 灵活的处理模式
- **仅放大 (upscale)**: 只进行图像放大，不进行质量增强
- **仅增强 (enhance)**: 只进行质量增强，不改变图像尺寸
- **全部处理 (all)**: 先放大再增强，获得最佳效果

### 4. 配置化管理
- JSON配置文件管理所有参数
- 支持命令行参数覆盖配置
- 自动生成默认配置文件

## 安装依赖

```bash
pip install opencv-python
pip install pillow
pip install numpy
```

## 使用方法

### 1. 基本使用

```bash
# 使用默认配置处理 input_images/ 文件夹中的所有图片
python qsy_hd_enhancer.py

# 指定输入和输出文件夹
python qsy_hd_enhancer.py --input /path/to/input --output /path/to/output

# 指定放大倍数
python qsy_hd_enhancer.py --factor 4

# 指定处理模式
python qsy_hd_enhancer.py --mode enhance

# 指定保存质量
python qsy_hd_enhancer.py --quality 100
```

### 2. 命令行参数

- `--input`: 输入文件夹路径 (默认: input_images/)
- `--output`: 输出文件夹路径 (默认: output_images/)
- `--config`: 配置文件路径 (默认: hd_config.json)
- `--factor`: 放大倍数 (默认: 2)
- `--mode`: 处理模式 (upscale/enhance/all, 默认: all)
- `--quality`: 保存质量 1-100 (默认: 95)

### 3. 配置文件说明

配置文件 `hd_config.json` 包含以下参数：

```json
{
  "upscale_factor": 2,           // 放大倍数
  "enhancement_mode": "all",     // 处理模式
  "save_quality": 95,            // 保存质量
  "algorithms": {
    "upscale": "esrgan_sim",     // 放大算法
    "enhance": "advanced"        // 增强算法
  },
  "enhancement_params": {
    "sharpness_radius": 2,       // 锐化半径
    "sharpness_percent": 150,    // 锐化强度
    "sharpness_threshold": 3,    // 锐化阈值
    "contrast_factor": 1.2,      // 对比度因子
    "color_factor": 1.1,         // 色彩饱和度因子
    "brightness_factor": 1.05    // 亮度因子
  },
  "esrgan_params": {
    "sharpening_kernel": [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]],  // 锐化核
    "blend_ratio": 0.3           // 混合比例
  }
}
```

## 支持的图片格式

- PNG
- JPG/JPEG
- BMP
- TIFF
- WebP

## 使用示例

### 示例1: 处理低分辨率图片
```bash
# 将图片放大2倍并增强质量
python qsy_hd_enhancer.py --factor 2 --mode all
```

### 示例2: 仅增强图片质量
```bash
# 不改变尺寸，仅增强图片质量
python qsy_hd_enhancer.py --mode enhance
```

### 示例3: 高质量输出
```bash
# 使用最高质量保存
python qsy_hd_enhancer.py --quality 100
```

## 算法说明

### 放大算法对比

1. **双三次插值**: 速度快，适合一般用途
2. **Lanczos插值**: 质量好，适合需要保持细节的图片
3. **ESRGAN模拟**: 效果最佳，通过锐化增强细节，适合需要最高质量的场景

### 增强算法对比

1. **基础增强**: 仅锐化，处理速度快
2. **高级增强**: 综合处理，平衡效果和速度
3. **超级增强**: 效果最佳，但处理时间较长

## 性能优化建议

1. **批量处理**: 将多张图片放在同一文件夹中批量处理
2. **算法选择**: 根据需求选择合适的算法组合
3. **质量设置**: 根据需要调整保存质量，平衡文件大小和效果

## 注意事项

1. 处理大图片时可能需要较长时间
2. 超级增强模式会显著增加处理时间
3. 建议在处理前备份原始文件
4. 输出文件会添加 "hd_" 前缀

## 故障排除

如果遇到问题，请检查：
1. 依赖包是否正确安装
2. 输入文件夹是否存在且包含支持的图片格式
3. 输出文件夹是否有写入权限
4. 配置文件格式是否正确

## 技术原理

- **图像放大**: 使用OpenCV的插值算法进行图像放大
- **质量增强**: 结合PIL和OpenCV的图像处理功能
- **细节增强**: 通过锐化滤波和边缘保持算法增强细节
- **色彩优化**: 通过对比度、饱和度和亮度调整优化视觉效果
