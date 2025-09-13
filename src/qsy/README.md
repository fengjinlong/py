# QSY 去水印工具集

这是一个专门用于去除水印的Python工具集，支持处理Gemini和JM平台的图片和视频水印。

## 功能概述

本工具集包含三个主要脚本，分别处理不同类型的水印：

1. **qsy_tp_gemini.py** - 处理Gemini平台图片水印
2. **qsy_sp_gemini.py** - 处理Gemini平台视频水印  
3. **qsy_sp_jm.py** - 处理JM平台视频水印

## 文件结构

```
qsy/
├── README.md                 # 本说明文件
├── qsy_tp_gemini.py         # Gemini图片去水印脚本
├── qsy_sp_gemini.py         # Gemini视频去水印脚本
├── qsy_sp_jm.py             # JM视频去水印脚本
├── input_images/            # 输入图片文件夹
├── output_images/           # 输出图片文件夹
├── input_videos/            # 输入视频文件夹
└── output_videos/           # 输出视频文件夹
```

## 脚本详细说明

### 1. qsy_tp_gemini.py - Gemini图片去水印

**功能**: 使用OpenCV的修复算法去除Gemini平台图片中的水印

**特点**:
- 支持多种图片格式：PNG, JPG, JPEG, BMP, TIFF
- 使用`cv2.inpaint`算法智能修复水印区域
- 自动调整坐标以适应不同尺寸的图片

**使用方法**:
1. 将需要处理的图片放入`input_images/`文件夹
2. 运行脚本：`python qsy_tp_gemini.py`
3. 处理后的图片将保存在`output_images/`文件夹

**配置参数**:
```python
# 水印区域坐标 (x1, y1, x2, y2)
x1, y1 = 2648, 1360  # 左上角坐标
x2, y2 = 2766, 1480  # 右下角坐标
```

### 2. qsy_sp_gemini.py - Gemini视频去水印

**功能**: 使用高斯模糊处理Gemini平台视频中的水印

**特点**:
- 支持MP4和MOV视频格式
- 使用高斯模糊算法处理水印区域
- 可选择是否绘制红色框标记水印位置（用于调试）
- 批量处理多个视频文件

**使用方法**:
1. 将需要处理的视频放入`input_videos/`文件夹
2. 运行脚本：`python qsy_sp_gemini.py`
3. 处理后的视频将保存在`output_videos/`文件夹

**配置参数**:
```python
# 水印区域配置
WATERMARK_AREAS = [
    {"x": 1200, "y": 660, "w": 50, "h": 36, "label": "WATERMARK1"},
    # 可添加更多水印区域
]

# 是否绘制红色框（调试用）
DRAW_WATERMARK_BOX = False
```

### 3. qsy_sp_jm.py - JM视频去水印

**功能**: 使用高斯模糊处理JM平台视频中的水印

**特点**:
- 支持MP4和MOV视频格式
- 可配置多个水印区域
- 使用高斯模糊算法处理水印
- 批量处理多个视频文件

**使用方法**:
1. 将需要处理的视频放入`input_videos/`文件夹
2. 运行脚本：`python qsy_sp_jm.py`
3. 处理后的视频将保存在`output_videos/`文件夹

**配置参数**:
```python
# 水印区域配置
WATERMARK_AREAS = [
    {"x": 995, "y": 610, "w": 218, "h": 78, "label": "WATERMARK1"},
    {"x": 10, "y": 10, "w": 80, "h": 42, "label": "WATERMARK2"},
    # 可添加更多水印区域
]
```

## 安装依赖

在运行脚本之前，请确保安装以下Python包：

```bash
pip install opencv-python
pip install moviepy
pip install numpy
```

## 使用步骤

### 处理图片水印
1. 将图片放入`input_images/`文件夹
2. 根据实际水印位置修改`qsy_tp_gemini.py`中的坐标参数
3. 运行：`python qsy_tp_gemini.py`
4. 在`output_images/`文件夹中查看处理结果

### 处理视频水印
1. 将视频放入`input_videos/`文件夹
2. 根据实际水印位置修改对应脚本中的`WATERMARK_AREAS`参数
3. 运行对应的脚本：
   - Gemini视频：`python qsy_sp_gemini.py`
   - JM视频：`python qsy_sp_jm.py`
4. 在`output_videos/`文件夹中查看处理结果

## 注意事项

1. **坐标调整**: 不同平台的水印位置可能不同，请根据实际情况调整坐标参数
2. **水印区域**: 建议先用调试模式（绘制红色框）确认水印区域位置
3. **文件格式**: 确保输入文件格式被脚本支持
4. **处理时间**: 视频处理可能需要较长时间，请耐心等待
5. **备份**: 建议在处理前备份原始文件

## 技术原理

- **图片去水印**: 使用OpenCV的`inpaint`算法，通过周围像素信息智能修复水印区域
- **视频去水印**: 使用高斯模糊算法，对水印区域进行模糊处理，降低水印的可见性

## 自定义配置

每个脚本都提供了详细的配置参数，您可以根据实际需求调整：

- 水印区域坐标和大小
- 模糊强度（高斯模糊核大小）
- 是否显示调试信息
- 输出文件格式和质量

## 故障排除

如果遇到问题，请检查：
1. 依赖包是否正确安装
2. 输入文件路径是否正确
3. 水印区域坐标是否准确
4. 文件权限是否足够
