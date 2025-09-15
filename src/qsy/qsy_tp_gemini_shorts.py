import cv2
import os
import numpy as np

folder = 'input_images/'
output_folder = 'output_images/'

# 创建输出文件夹（如果不存在）
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 定义水印区域坐标 (x1, y1, x2, y2)
# 这里设置为图片右下角的一个矩形区域，您可以根据实际情况调整
x1, y1 = 1358 , 2645  # 左上角坐标
x2, y2 = 1481 , 2768  # 右下角坐标

for filename in os.listdir(folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        img_path = os.path.join(folder, filename)
        img = cv2.imread(img_path)
        
        if img is not None:
            # 调整坐标以适应图片尺寸
            h, w = img.shape[:2]
            x1_adj = min(x1, w-1)
            y1_adj = min(y1, h-1)
            x2_adj = min(x2, w)
            y2_adj = min(y2, h)
            
            # 创建掩码
            mask = np.zeros(img.shape[:2], np.uint8)
            cv2.rectangle(mask, (x1_adj, y1_adj), (x2_adj, y2_adj), 255, -1)
            
            # 使用修复算法去除水印
            dst = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
            
            # 保存处理后的图片
            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, dst)
            print(f"已处理: {filename}")
        else:
            print(f"无法读取图片: {filename}")
    else:
        print(f"跳过非图片文件: {filename}")
