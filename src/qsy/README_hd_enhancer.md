# QSY 图片高清化工具

这是一个专门用于图片高清化处理的Python工具，结合了多种先进的图像处理算法，能够显著提升图片的清晰度和质量。

## 功能特点

### 1. 完全配置化管理
- **所有参数从配置文件读取** - 程序不包含任何硬编码的默认值
- **JSON配置文件** - 使用 `hd_config.json` 管理所有参数
- **命令行覆盖** - 支持通过命令行参数覆盖配置文件设置
- **配置验证** - 自动验证配置文件格式和完整性

### 2. 多种放大算法
- **双三次插值 (Bicubic)**: 经典的图像放大算法，平衡速度和质量
- **Lanczos插值**: 高质量的图像放大算法，细节保持更好
- **ESRGAN模拟**: 模拟ESRGAN深度学习算法的效果，通过锐化增强细节

### 3. 多种增强模式
- **基础增强**: 仅进行锐化处理
- **高级增强**: 锐化 + 对比度 + 色彩饱和度 + 亮度调整
- **超级增强**: 高级增强 + 双边滤波 + 去噪 + 拉普拉斯锐化

### 4. 灵活的处理模式
- **仅放大 (upscale)**: 只进行图像放大，不进行质量增强
- **仅增强 (enhance)**: 只进行质量增强，不改变图像尺寸
- **全部处理 (all)**: 先放大再增强，获得最佳效果

## 安装依赖

```bash
pip install opencv-python
pip install pillow
pip install numpy
```

## 配置文件说明

**重要**: 程序完全依赖 `hd_config.json` 配置文件，不包含任何硬编码的默认值。

### 配置文件结构

```json
{
  "upscale_factor": 2,           // 放大倍数
  "enhancement_mode": "all",     // 处理模式: upscale/enhance/all
  "save_quality": 95,            // 保存质量 1-100
  "algorithms": {
    "upscale": "esrgan_sim",     // 放大算法: bicubic/lanczos/esrgan_sim
    "enhance": "advanced"        // 增强算法: basic/advanced/super
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
  },
  "bilateral_filter": {
    "d": 20,                     // 双边滤波直径
    "sigma_color": 80,           // 颜色空间标准差
    "sigma_space": 80            // 坐标空间标准差
  },
  "denoising_params": {
    "h": 10,                     // 去噪强度
    "h_color": 10,               // 颜色去噪强度
    "template_window_size": 7,   // 模板窗口大小
    "search_window_size": 21     // 搜索窗口大小
  },
  "laplacian_sharpening": {
    "alpha": 0.3                 // 拉普拉斯锐化强度
  }
}
```

### 配置文件要求

1. **必须存在**: 程序启动时配置文件必须存在
2. **格式正确**: 必须是有效的JSON格式
3. **参数完整**: 必须包含所有必需的参数
4. **编码正确**: 必须使用UTF-8编码

## 使用方法

### 1. 基本使用

```bash
# 使用配置文件中的设置处理图片
python3 qsy_hd_enhancer.py

# 指定输入和输出文件夹
python3 qsy_hd_enhancer.py --input /path/to/input --output /path/to/output

# 使用自定义配置文件
python3 qsy_hd_enhancer.py --config /path/to/config.json
```

### 2. 命令行参数覆盖

```bash
# 覆盖配置文件中的放大倍数
python3 qsy_hd_enhancer.py --factor 4

# 覆盖配置文件中的处理模式
python3 qsy_hd_enhancer.py --mode enhance

# 覆盖配置文件中的保存质量
python3 qsy_hd_enhancer.py --quality 100

# 组合使用多个参数
python3 qsy_hd_enhancer.py --factor 4 --mode all --quality 100
```

### 3. 命令行参数说明

- `--input`: 输入文件夹路径 (默认: input_images/)
- `--output`: 输出文件夹路径 (默认: output_images/)
- `--config`: 配置文件路径 (默认: hd_config.json)
- `--factor`: 放大倍数 (覆盖配置文件中的设置)
- `--mode`: 处理模式 (upscale/enhance/all, 覆盖配置文件中的设置)
- `--quality`: 保存质量 1-100 (覆盖配置文件中的设置)

## 支持的图片格式

- PNG
- JPG/JPEG
- BMP
- TIFF
- WebP

## 使用示例

### 示例1: 使用默认配置
```bash
# 确保 hd_config.json 存在，然后运行
python3 qsy_hd_enhancer.py
```

### 示例2: 自定义配置
```bash
# 创建自定义配置文件
cp hd_config.json my_config.json
# 编辑 my_config.json 文件
# 使用自定义配置运行
python3 qsy_hd_enhancer.py --config my_config.json
```

### 示例3: 命令行覆盖
```bash
# 使用配置文件，但临时改变放大倍数
python3 qsy_hd_enhancer.py --factor 4
```

## 算法说明

### 放大算法对比

1. **双三次插值 (bicubic)**: 速度快，适合一般用途
2. **Lanczos插值 (lanczos)**: 质量好，适合需要保持细节的图片
3. **ESRGAN模拟 (esrgan_sim)**: 效果最佳，通过锐化增强细节，适合需要最高质量的场景

### 增强算法对比

1. **基础增强 (basic)**: 仅锐化，处理速度快
2. **高级增强 (advanced)**: 综合处理，平衡效果和速度
3. **超级增强 (super)**: 效果最佳，但处理时间较长

## 错误处理

### 配置文件错误
- **文件不存在**: 程序会报错并退出
- **格式错误**: 程序会报错并退出
- **参数缺失**: 程序会报错并退出

### 图片处理错误
- **读取失败**: 跳过该文件，继续处理其他文件
- **处理失败**: 记录错误日志，继续处理其他文件
- **保存失败**: 记录错误日志，继续处理其他文件

## 性能优化建议

1. **批量处理**: 将多张图片放在同一文件夹中批量处理
2. **算法选择**: 根据需求选择合适的算法组合
3. **质量设置**: 根据需要调整保存质量，平衡文件大小和效果
4. **配置文件**: 预先配置好所有参数，避免运行时修改

## 注意事项

1. **配置文件必需**: 程序启动前必须确保配置文件存在且格式正确
2. **处理大图片**: 处理大图片时可能需要较长时间
3. **超级增强模式**: 会显著增加处理时间
4. **备份原始文件**: 建议在处理前备份原始文件
5. **输出文件**: 输出文件会添加 "hd_" 前缀

## 故障排除

### 常见问题

1. **配置文件不存在**
   ```
   错误: 配置文件不存在: hd_config.json
   解决: 确保 hd_config.json 文件存在于程序目录中
   ```

2. **配置文件格式错误**
   ```
   错误: 配置文件格式错误: ...
   解决: 检查JSON格式是否正确，可以使用在线JSON验证工具
   ```

3. **参数缺失**
   ```
   错误: 配置文件加载失败: ...
   解决: 确保配置文件包含所有必需的参数
   ```

### 调试建议

1. 使用 `--help` 查看所有可用参数
2. 检查配置文件格式和内容
3. 查看详细的错误日志
4. 测试小批量图片处理

## 技术原理

- **图像放大**: 使用OpenCV的插值算法进行图像放大
- **质量增强**: 结合PIL和OpenCV的图像处理功能
- **细节增强**: 通过锐化滤波和边缘保持算法增强细节
- **色彩优化**: 通过对比度、饱和度和亮度调整优化视觉效果
- **配置管理**: 完全基于JSON配置文件的参数管理
