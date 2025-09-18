import cv2
import os
import numpy as np
import json
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WatermarkRemover:
    """多水印区域去除器"""
    
    def __init__(self, input_folder: str = 'input_images/', 
                 output_folder: str = 'output_images/',
                 config_file: str = 'watermark_config.json'):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.config_file = Path(config_file)
        
        # 创建输出文件夹
        self.output_folder.mkdir(exist_ok=True)
        
        # 加载配置
        self.watermark_regions = self.load_config()
        
        # 支持的图片格式
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    
    def load_config(self) -> List[Dict]:
        """加载水印区域配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('watermark_regions', [])
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}，使用默认配置")
        
        # 默认配置
        default_config = {
            "watermark_regions": [
                {
                    "name": "右下角水印",
                    "coordinates": [2648, 1360, 2766, 1480],
                    "enabled": True
                }
            ]
        }
        
        # 保存默认配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        return default_config["watermark_regions"]
    
    def validate_coordinates(self, coords: List[int], img_shape: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """验证并调整坐标以适应图片尺寸"""
        if len(coords) != 4:
            raise ValueError("坐标必须包含4个值: [x1, y1, x2, y2]")
        
        x1, y1, x2, y2 = coords
        h, w = img_shape[:2]
        
        # 确保坐标顺序正确
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # 调整坐标以适应图片尺寸
        x1_adj = max(0, min(x1, w-1))
        y1_adj = max(0, min(y1, h-1))
        x2_adj = max(x1_adj+1, min(x2, w))
        y2_adj = max(y1_adj+1, min(y2, h))
        
        return x1_adj, y1_adj, x2_adj, y2_adj
    
    def create_combined_mask(self, img_shape: Tuple[int, int]) -> np.ndarray:
        """创建包含所有水印区域的组合掩码"""
        mask = np.zeros(img_shape[:2], np.uint8)
        
        for region in self.watermark_regions:
            if not region.get('enabled', True):
                continue
                
            try:
                coords = region['coordinates']
                x1, y1, x2, y2 = self.validate_coordinates(coords, img_shape)
                
                # 在掩码上标记水印区域
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
                logger.info(f"添加水印区域: {region.get('name', '未命名')} - ({x1},{y1},{x2},{y2})")
                
            except Exception as e:
                logger.error(f"处理水印区域失败 {region.get('name', '未命名')}: {e}")
                continue
        
        return mask
    
    def remove_watermarks(self, img: np.ndarray, 
                         inpaint_method: int = cv2.INPAINT_TELEA,
                         inpaint_radius: int = 3) -> np.ndarray:
        """使用指定方法去除水印"""
        mask = self.create_combined_mask(img.shape)
        
        if np.sum(mask) == 0:
            logger.warning("没有找到有效的水印区域")
            return img
        
        # 使用修复算法去除水印
        result = cv2.inpaint(img, mask, inpaint_radius, inpaint_method)
        
        # 记录处理的像素数量
        pixel_count = np.sum(mask > 0)
        logger.info(f"处理了 {pixel_count} 个水印像素")
        
        return result
    
    def process_single_image(self, img_path: Path) -> bool:
        """处理单张图片"""
        try:
            # 读取图片
            img = cv2.imread(str(img_path))
            if img is None:
                logger.error(f"无法读取图片: {img_path}")
                return False
            
            logger.info(f"开始处理: {img_path.name} (尺寸: {img.shape})")
            
            # 去除水印
            processed_img = self.remove_watermarks(img)
            
            # 保存处理后的图片
            output_path = self.output_folder / img_path.name
            success = cv2.imwrite(str(output_path), processed_img)
            
            if success:
                logger.info(f"成功保存: {output_path}")
                return True
            else:
                logger.error(f"保存失败: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"处理图片失败 {img_path}: {e}")
            return False
    
    def process_all_images(self) -> Dict[str, int]:
        """处理所有图片"""
        if not self.input_folder.exists():
            logger.error(f"输入文件夹不存在: {self.input_folder}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        # 获取所有图片文件
        image_files = [f for f in self.input_folder.iterdir() 
                      if f.suffix.lower() in self.supported_formats]
        
        if not image_files:
            logger.warning(f"在 {self.input_folder} 中没有找到支持的图片文件")
            return results
        
        logger.info(f"找到 {len(image_files)} 个图片文件")
        
        # 处理每个图片
        for img_path in image_files:
            if self.process_single_image(img_path):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def add_watermark_region(self, name: str, coordinates: List[int], enabled: bool = True):
        """动态添加水印区域"""
        region = {
            "name": name,
            "coordinates": coordinates,
            "enabled": enabled
        }
        self.watermark_regions.append(region)
        self.save_config()
        logger.info(f"添加水印区域: {name}")
    
    def save_config(self):
        """保存配置到文件"""
        config = {"watermark_regions": self.watermark_regions}
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    print("=== 多水印区域去除工具 ===")
    
    # 创建水印去除器
    remover = WatermarkRemover()
    
    # 显示当前配置
    print(f"\n当前配置的水印区域:")
    for i, region in enumerate(remover.watermark_regions, 1):
        status = "启用" if region.get('enabled', True) else "禁用"
        coords = region['coordinates']
        print(f"  {i}. {region.get('name', '未命名')} - {status} - 坐标: ({coords[0]},{coords[1]},{coords[2]},{coords[3]})")
    
    # 处理所有图片
    print(f"\n开始处理图片...")
    results = remover.process_all_images()
    
    # 显示结果
    print(f"\n处理完成!")
    print(f"成功: {results['success']} 张")
    print(f"失败: {results['failed']} 张")
    print(f"跳过: {results['skipped']} 张")
    
    if results['success'] > 0:
        print(f"\n处理后的图片已保存到: {remover.output_folder}")

if __name__ == "__main__":
    main()
