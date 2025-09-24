import cv2
import os
import numpy as np
import json

folder = 'input_images/'
output_folder = 'output_images/'
config_file = 'watermark_config.json'

# 创建输出文件夹（如果不存在）
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 默认水印区域配置 - 支持多个水印点
# 1. 17 , 21
# 2. 177 , 82
# 3. 714 , 1581
# 4. 913 , 1637
default_watermarks = [
    {
        "name": "右下角水印1",
        "coordinates": [17, 21, 177, 82],  # [x1, y1, x2, y2]
        "enabled": True
    },
    {
        "name": "水印点2", 
        "coordinates": [714, 1581, 913, 1637],  # [x1, y1, x2, y2]
        "enabled": True
    }
]

def load_watermark_config():
    """加载水印配置文件，如果不存在则创建默认配置"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"已加载配置文件: {config_file}")
                return config.get('watermarks', default_watermarks)
        except Exception as e:
            print(f"配置文件加载失败: {e}，使用默认配置")
            return default_watermarks
    else:
        # 创建默认配置文件
        config = {
            "description": "水印区域配置文件",
            "watermarks": default_watermarks
        }
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"已创建默认配置文件: {config_file}")
        except Exception as e:
            print(f"创建配置文件失败: {e}")
        return default_watermarks

def process_watermarks(img, watermarks):
    """处理多个水印区域"""
    h, w = img.shape[:2]
    result_img = img.copy()
    
    for i, watermark in enumerate(watermarks):
        if not watermark.get('enabled', True):
            print(f"跳过禁用的水印: {watermark.get('name', f'水印{i+1}')}")
            continue
            
        coords = watermark['coordinates']
        if len(coords) != 4:
            print(f"水印 {watermark.get('name', f'水印{i+1}')} 坐标格式错误，跳过")
            continue
            
        x1, y1, x2, y2 = coords
        
        # 调整坐标以适应图片尺寸
        x1_adj = max(0, min(x1, w-1))
        y1_adj = max(0, min(y1, h-1))
        x2_adj = max(x1_adj+1, min(x2, w))
        y2_adj = max(y1_adj+1, min(y2, h))
        
        # 检查坐标有效性
        if x1_adj >= x2_adj or y1_adj >= y2_adj:
            print(f"水印 {watermark.get('name', f'水印{i+1}')} 坐标无效，跳过")
            continue
        
        # 创建掩码
        mask = np.zeros(img.shape[:2], np.uint8)
        cv2.rectangle(mask, (x1_adj, y1_adj), (x2_adj-1, y2_adj-1), 255, -1)
        
        # 使用修复算法去除水印
        dst = cv2.inpaint(result_img, mask, 3, cv2.INPAINT_TELEA)
        result_img = dst
        
        print(f"已处理水印: {watermark.get('name', f'水印{i+1}')} - 坐标: ({x1_adj},{y1_adj}) 到 ({x2_adj-1},{y2_adj-1})")
    
    return result_img

# 加载水印配置
watermarks = load_watermark_config()

print(f"共加载 {len(watermarks)} 个水印配置")
for i, wm in enumerate(watermarks):
    status = "启用" if wm.get('enabled', True) else "禁用"
    print(f"  {i+1}. {wm.get('name', f'水印{i+1}')} - {status}")

# 处理图片
processed_count = 0
for filename in os.listdir(folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        img_path = os.path.join(folder, filename)
        img = cv2.imread(img_path)
        
        if img is not None:
            print(f"\n开始处理: {filename}")
            # 处理多个水印
            result_img = process_watermarks(img, watermarks)
            
            # 保存处理后的图片
            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, result_img)
            print(f"已保存: {filename}")
            processed_count += 1
        else:
            print(f"无法读取图片: {filename}")
    else:
        print(f"跳过非图片文件: {filename}")

print(f"\n处理完成！共处理了 {processed_count} 张图片")
