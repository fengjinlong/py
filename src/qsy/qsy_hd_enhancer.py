import cv2
import os
import numpy as np
import json
import logging
import argparse
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageHDEnhancer:
    """图片高清化增强器"""
    
    def __init__(self, input_folder: str = 'input_images/', 
                 output_folder: str = 'output_images/',
                 config_file: str = 'hd_config.json'):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.config_file = Path(config_file)
        
        # 创建输出文件夹
        self.output_folder.mkdir(exist_ok=True)
        
        # 加载配置
        self.config = self.load_config()
        
        # 支持的图片格式
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        
        # 处理统计
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'processing_time': 0
        }
    
    def load_config(self) -> Dict:
        """加载高清化配置"""
        default_config = {
            "upscale_factor": 2,
            "enhancement_mode": "all",  # "upscale", "enhance", "all"
            "save_quality": 95,
            "algorithms": {
                "upscale": "esrgan_sim",  # "bicubic", "lanczos", "esrgan_sim"
                "enhance": "advanced"     # "basic", "advanced", "super"
            },
            "enhancement_params": {
                "sharpness_radius": 2,
                "sharpness_percent": 150,
                "sharpness_threshold": 3,
                "contrast_factor": 1.2,
                "color_factor": 1.1,
                "brightness_factor": 1.05
            },
            "esrgan_params": {
                "sharpening_kernel": [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]],
                "blend_ratio": 0.3
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和用户配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}，使用默认配置")
        
        # 保存默认配置
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def upscale_bicubic(self, img: np.ndarray, factor: float) -> np.ndarray:
        """使用双三次插值进行放大"""
        h, w = img.shape[:2]
        new_h, new_w = int(h * factor), int(w * factor)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    def upscale_lanczos(self, img: np.ndarray, factor: float) -> np.ndarray:
        """使用Lanczos插值进行放大"""
        h, w = img.shape[:2]
        new_h, new_w = int(h * factor), int(w * factor)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    def upscale_esrgan_simulation(self, img: np.ndarray, factor: float) -> np.ndarray:
        """模拟ESRGAN效果的放大算法"""
        h, w = img.shape[:2]
        new_h, new_w = int(h * factor), int(w * factor)
        
        # 先进行双三次插值
        upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # 应用锐化滤波器增强细节
        kernel = np.array(self.config["esrgan_params"]["sharpening_kernel"])
        sharpened = cv2.filter2D(upscaled, -1, kernel)
        
        # 混合原图和锐化图
        blend_ratio = self.config["esrgan_params"]["blend_ratio"]
        enhanced = cv2.addWeighted(upscaled, 1 - blend_ratio, sharpened, blend_ratio, 0)
        
        return enhanced
    
    def enhance_basic(self, img: np.ndarray) -> np.ndarray:
        """基础图片增强"""
        # 转换为PIL图像进行增强
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # 锐化
        sharpened = pil_img.filter(ImageFilter.UnsharpMask(
            radius=self.config["enhancement_params"]["sharpness_radius"],
            percent=self.config["enhancement_params"]["sharpness_percent"],
            threshold=self.config["enhancement_params"]["sharpness_threshold"]
        ))
        
        # 转换回OpenCV格式
        enhanced = cv2.cvtColor(np.array(sharpened), cv2.COLOR_RGB2BGR)
        return enhanced
    
    def enhance_advanced(self, img: np.ndarray) -> np.ndarray:
        """高级图片增强"""
        # 转换为PIL图像进行增强
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # 1. 锐化
        sharpened = pil_img.filter(ImageFilter.UnsharpMask(
            radius=self.config["enhancement_params"]["sharpness_radius"],
            percent=self.config["enhancement_params"]["sharpness_percent"],
            threshold=self.config["enhancement_params"]["sharpness_threshold"]
        ))
        
        # 2. 对比度增强
        enhancer = ImageEnhance.Contrast(sharpened)
        contrast_enhanced = enhancer.enhance(self.config["enhancement_params"]["contrast_factor"])
        
        # 3. 色彩饱和度增强
        color_enhancer = ImageEnhance.Color(contrast_enhanced)
        color_enhanced = color_enhancer.enhance(self.config["enhancement_params"]["color_factor"])
        
        # 4. 亮度微调
        brightness_enhancer = ImageEnhance.Brightness(color_enhanced)
        brightness_enhanced = brightness_enhancer.enhance(self.config["enhancement_params"]["brightness_factor"])
        
        # 转换回OpenCV格式
        enhanced = cv2.cvtColor(np.array(brightness_enhanced), cv2.COLOR_RGB2BGR)
        return enhanced
    
    def enhance_super(self, img: np.ndarray) -> np.ndarray:
        """超级增强模式"""
        # 先进行高级增强
        enhanced = self.enhance_advanced(img)
        
        # 额外的OpenCV处理
        # 1. 双边滤波保持边缘
        bilateral = cv2.bilateralFilter(enhanced, 20, 80, 80)
        
        # 2. 非局部均值去噪
        denoised = cv2.fastNlMeansDenoisingColored(bilateral, None, 10, 10, 7, 21)
        
        # 3. 拉普拉斯锐化
        laplacian = cv2.Laplacian(denoised, cv2.CV_64F)
        laplacian = np.uint8(np.absolute(laplacian))
        sharpened = cv2.addWeighted(denoised, 1.0, laplacian, 0.3, 0)
        
        return sharpened
    
    def process_image(self, img: np.ndarray, filename: str) -> Optional[np.ndarray]:
        """处理单张图片"""
        try:
            h, w = img.shape[:2]
            logger.info(f"处理图片: {filename} (原始尺寸: {w}x{h})")
            
            mode = self.config["enhancement_mode"]
            factor = self.config["upscale_factor"]
            
            if mode == "upscale":
                # 仅放大
                algorithm = self.config["algorithms"]["upscale"]
                if algorithm == "bicubic":
                    processed = self.upscale_bicubic(img, factor)
                elif algorithm == "lanczos":
                    processed = self.upscale_lanczos(img, factor)
                elif algorithm == "esrgan_sim":
                    processed = self.upscale_esrgan_simulation(img, factor)
                else:
                    processed = self.upscale_bicubic(img, factor)
                    
            elif mode == "enhance":
                # 仅增强
                algorithm = self.config["algorithms"]["enhance"]
                if algorithm == "basic":
                    processed = self.enhance_basic(img)
                elif algorithm == "advanced":
                    processed = self.enhance_advanced(img)
                elif algorithm == "super":
                    processed = self.enhance_super(img)
                else:
                    processed = self.enhance_advanced(img)
                    
            elif mode == "all":
                # 放大+增强
                # 先放大
                upscale_algorithm = self.config["algorithms"]["upscale"]
                if upscale_algorithm == "bicubic":
                    upscaled = self.upscale_bicubic(img, factor)
                elif upscale_algorithm == "lanczos":
                    upscaled = self.upscale_lanczos(img, factor)
                elif upscale_algorithm == "esrgan_sim":
                    upscaled = self.upscale_esrgan_simulation(img, factor)
                else:
                    upscaled = self.upscale_esrgan_simulation(img, factor)
                
                # 再增强
                enhance_algorithm = self.config["algorithms"]["enhance"]
                if enhance_algorithm == "basic":
                    processed = self.enhance_basic(upscaled)
                elif enhance_algorithm == "advanced":
                    processed = self.enhance_advanced(upscaled)
                elif enhance_algorithm == "super":
                    processed = self.enhance_super(upscaled)
                else:
                    processed = self.enhance_advanced(upscaled)
            else:
                processed = img
            
            new_h, new_w = processed.shape[:2]
            logger.info(f"处理完成: {filename} (处理后尺寸: {new_w}x{new_h})")
            return processed
            
        except Exception as e:
            logger.error(f"处理图片失败: {filename} - 错误: {str(e)}")
            return None
    
    def save_image(self, img: np.ndarray, filename: str) -> bool:
        """保存处理后的图片"""
        try:
            output_path = self.output_folder / f"hd_{filename}"
            
            # 根据文件格式选择保存方法
            if filename.lower().endswith('.png'):
                success = cv2.imwrite(str(output_path), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            else:
                quality = self.config["save_quality"]
                success = cv2.imwrite(str(output_path), img, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            if success:
                logger.info(f"✓ 保存成功: {output_path}")
                return True
            else:
                logger.error(f"✗ 保存失败: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"保存图片失败: {filename} - 错误: {str(e)}")
            return False
    
    def process_all_images(self):
        """批量处理所有图片"""
        logger.info("=== QSY 图片高清化工具 ===")
        logger.info(f"输入文件夹: {self.input_folder}")
        logger.info(f"输出文件夹: {self.output_folder}")
        logger.info(f"放大倍数: {self.config['upscale_factor']}x")
        logger.info(f"增强模式: {self.config['enhancement_mode']}")
        logger.info(f"保存质量: {self.config['save_quality']}")
        logger.info("-" * 50)
        
        # 统计文件数量
        image_files = []
        for file_path in self.input_folder.iterdir():
            if file_path.suffix.lower() in self.supported_formats:
                image_files.append(file_path)
        
        self.stats['total_files'] = len(image_files)
        logger.info(f"发现 {self.stats['total_files']} 个图片文件")
        logger.info("-" * 50)
        
        if not image_files:
            logger.warning("未找到支持的图片文件")
            return
        
        # 开始处理
        start_time = time.time()
        
        for file_path in image_files:
            filename = file_path.name
            logger.info(f"正在处理: {filename}")
            
            try:
                # 读取图片
                img = cv2.imread(str(file_path))
                
                if img is not None:
                    # 处理图片
                    processed_img = self.process_image(img, filename)
                    
                    if processed_img is not None:
                        # 保存图片
                        if self.save_image(processed_img, filename):
                            self.stats['processed_files'] += 1
                        else:
                            self.stats['failed_files'] += 1
                    else:
                        self.stats['failed_files'] += 1
                else:
                    logger.error(f"✗ 无法读取图片: {filename}")
                    self.stats['failed_files'] += 1
                    
            except Exception as e:
                logger.error(f"✗ 处理失败: {filename} - 错误: {str(e)}")
                self.stats['failed_files'] += 1
        
        # 计算处理时间
        self.stats['processing_time'] = time.time() - start_time
        
        # 输出统计信息
        logger.info("-" * 50)
        logger.info(f"处理完成! 成功处理 {self.stats['processed_files']}/{self.stats['total_files']} 个文件")
        logger.info(f"失败文件: {self.stats['failed_files']} 个")
        logger.info(f"总处理时间: {self.stats['processing_time']:.2f} 秒")
        logger.info(f"输出文件保存在: {self.output_folder}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='QSY 图片高清化工具')
    parser.add_argument('--input', type=str, default='input_images/', 
                       help='输入文件夹路径 (默认: input_images/)')
    parser.add_argument('--output', type=str, default='output_images/', 
                       help='输出文件夹路径 (默认: output_images/)')
    parser.add_argument('--config', type=str, default='hd_config.json', 
                       help='配置文件路径 (默认: hd_config.json)')
    parser.add_argument('--factor', type=int, default=2, 
                       help='放大倍数 (默认: 2)')
    parser.add_argument('--mode', choices=['upscale', 'enhance', 'all'], default='all', 
                       help='处理模式: upscale(仅放大), enhance(仅增强), all(放大+增强)')
    parser.add_argument('--quality', type=int, default=95, 
                       help='保存质量 1-100 (默认: 95)')
    
    args = parser.parse_args()
    
    # 创建增强器实例
    enhancer = ImageHDEnhancer(
        input_folder=args.input,
        output_folder=args.output,
        config_file=args.config
    )
    
    # 更新配置
    enhancer.config['upscale_factor'] = args.factor
    enhancer.config['enhancement_mode'] = args.mode
    enhancer.config['save_quality'] = max(1, min(100, args.quality))
    
    # 保存更新后的配置
    enhancer.save_config(enhancer.config)
    
    # 开始处理
    enhancer.process_all_images()

if __name__ == "__main__":
    main()
