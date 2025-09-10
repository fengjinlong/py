#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量图片高清化处理脚本
支持多种超分辨率算法，包括Real-ESRGAN、ESRGAN等
"""

import os
import sys
import argparse
import time
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm
import cv2

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    REALESRGAN_AVAILABLE = True
except ImportError:
    REALESRGAN_AVAILABLE = False
    print("警告: Real-ESRGAN 未安装，将使用OpenCV的插值方法")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("警告: PyTorch 未安装，将使用CPU版本的Real-ESRGAN")

class ImageUpscaler:
    """图片高清化处理器"""
    
    def __init__(self, method='realesrgan', scale=4, device='auto'):
        self.method = method
        self.scale = scale
        self.device = device
        
        # 初始化Real-ESRGAN模型
        if method == 'realesrgan' and REALESRGAN_AVAILABLE:
            self._init_realesrgan()
        else:
            print(f"使用OpenCV插值方法进行{scale}x放大")
    
    def _init_realesrgan(self):
        """初始化Real-ESRGAN模型"""
        try:
            # 选择设备
            if self.device == 'auto':
                self.device = 'cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu'
            
            # 加载Real-ESRGAN模型
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=self.scale)
            model_path = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
            
            self.upsampler = RealESRGANer(
                scale=self.scale,
                model_path=model_path,
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=self.device != 'cpu'
            )
            print(f"Real-ESRGAN模型已加载，使用设备: {self.device}")
            
        except Exception as e:
            print(f"Real-ESRGAN初始化失败: {e}")
            print("回退到OpenCV插值方法")
            self.method = 'opencv'
    
    def upscale_image(self, image_path, output_path):
        """对单张图片进行高清化处理"""
        try:
            # 读取图片
            img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"无法读取图片: {image_path}")
            
            if self.method == 'realesrgan' and hasattr(self, 'upsampler'):
                # 使用Real-ESRGAN
                output, _ = self.upsampler.enhance(img, outscale=self.scale)
            else:
                # 使用OpenCV插值
                height, width = img.shape[:2]
                new_height, new_width = height * self.scale, width * self.scale
                output = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            # 保存结果
            cv2.imwrite(str(output_path), output)
            return True
            
        except Exception as e:
            print(f"处理图片 {image_path} 时出错: {e}")
            return False
    
    def batch_upscale(self, input_dir, output_dir, file_extensions=None):
        """批量处理图片"""
        if file_extensions is None:
            file_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片文件
        image_files = []
        for ext in file_extensions:
            image_files.extend(input_path.glob(f'*{ext}'))
            image_files.extend(input_path.glob(f'*{ext.upper()}'))
        
        if not image_files:
            print(f"在 {input_dir} 中未找到支持的图片文件")
            return
        
        print(f"找到 {len(image_files)} 张图片，开始处理...")
        
        # 处理每张图片
        success_count = 0
        for img_file in tqdm(image_files, desc="处理图片"):
            output_file = output_path / f"{img_file.stem}_upscaled{img_file.suffix}"
            
            if self.upscale_image(img_file, output_file):
                success_count += 1
        
        print(f"处理完成！成功处理 {success_count}/{len(image_files)} 张图片")
        print(f"输出目录: {output_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量图片高清化处理工具')
    parser.add_argument('input_dir', help='输入图片目录')
    parser.add_argument('-o', '--output', help='输出目录', default='./upscaled_images')
    parser.add_argument('-m', '--method', choices=['realesrgan', 'opencv'], 
                       default='realesrgan', help='处理方法')
    parser.add_argument('-s', '--scale', type=int, default=4, 
                       help='放大倍数 (2, 4, 8)')
    parser.add_argument('-d', '--device', choices=['auto', 'cpu', 'cuda'], 
                       default='auto', help='计算设备')
    parser.add_argument('--extensions', nargs='+', 
                       default=['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
                       help='支持的图片格式')
    
    args = parser.parse_args()
    
    # 检查输入目录
    if not os.path.exists(args.input_dir):
        print(f"错误: 输入目录不存在: {args.input_dir}")
        sys.exit(1)
    
    # 创建处理器
    upscaler = ImageUpscaler(
        method=args.method,
        scale=args.scale,
        device=args.device
    )
    
    # 开始批量处理
    start_time = time.time()
    upscaler.batch_upscale(args.input_dir, args.output, args.extensions)
    end_time = time.time()
    
    print(f"总耗时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    main()
