from moviepy import VideoFileClip
import cv2
import numpy as np
import os

# 定义多个水印区域 - 你可以在这里添加更多水印坐标
WATERMARK_AREAS = [
    {"x": 995, "y": 610, "w": 218, "h": 78, "label": "WATERMARK1"},  # 第一个水印
    {"x": 10, "y": 10, "w": 120, "h": 62, "label": "WATERMARK2"},  # 第二个水印 - 请根据实际情况修改坐标
    # 如果需要更多水印，可以继续添加
    # {"x": 500, "y": 300, "w": 150, "h": 40, "label": "WATERMARK3"},
]

# 是否在水印区域画红色框（True 开启 / False 关闭）
DRAW_WATERMARK_BOX = False

# 水印去除方法选择
REMOVAL_METHOD = "morphology"  # 可选: "gaussian_blur", "enhanced_blur", "super_enhanced", "inpainting", "morphology"

def remove_watermark_gaussian_blur(frame, area):
    """使用高斯模糊去除水印"""
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    roi = frame[y:y+h, x:x+w]
    # 使用更强的模糊参数
    blurred = cv2.GaussianBlur(roi, (101, 101), 0)
    return blurred

def remove_watermark_enhanced_blur(frame, area):
    """增强模糊方法 - 结合多种模糊技术"""
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    roi = frame[y:y+h, x:x+w]
    
    # 方法1: 多次高斯模糊
    blurred1 = cv2.GaussianBlur(roi, (151, 151), 0)
    blurred2 = cv2.GaussianBlur(blurred1, (101, 101), 0)
    
    # 方法2: 添加中值模糊去除噪声
    median = cv2.medianBlur(blurred2, 15)
    
    # 方法3: 双边滤波保持边缘但模糊细节
    bilateral = cv2.bilateralFilter(median, 20, 80, 80)
    
    return bilateral

def remove_watermark_super_enhanced(frame, area):
    """超级增强方法 - 专门针对顽固水印"""
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    roi = frame[y:y+h, x:x+w]
    
    # 步骤1: 极强高斯模糊
    blurred1 = cv2.GaussianBlur(roi, (201, 201), 0)
    blurred2 = cv2.GaussianBlur(blurred1, (151, 151), 0)
    blurred3 = cv2.GaussianBlur(blurred2, (101, 101), 0)
    
    # 步骤2: 中值模糊去除噪声和边缘
    median1 = cv2.medianBlur(blurred3, 21)
    median2 = cv2.medianBlur(median1, 15)
    
    # 步骤3: 双边滤波平滑
    bilateral = cv2.bilateralFilter(median2, 30, 100, 100)
    
    # 步骤4: 形态学开运算去除小噪点
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(bilateral, cv2.MORPH_OPEN, kernel)
    
    # 步骤5: 最终高斯模糊确保完全平滑
    final = cv2.GaussianBlur(opened, (81, 81), 0)
    
    return final

def remove_watermark_inpainting(frame, area):
    """使用图像修复技术去除水印"""
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    
    # 创建掩码
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mask[y:y+h, x:x+w] = 255
    
    # 使用图像修复
    inpainted = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
    return inpainted[y:y+h, x:x+w]

def remove_watermark_morphology(frame, area):
    """使用形态学操作去除水印"""
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    roi = frame[y:y+h, x:x+w]
    
    # 转换为灰度
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 创建掩码
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 形态学操作
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 应用掩码
    result = roi.copy()
    result[mask == 0] = [0, 0, 0]  # 黑色填充
    
    # 最后进行模糊处理
    blurred = cv2.GaussianBlur(result, (81, 81), 0)
    return blurred

def remove_watermark(frame):
    frame = frame.copy()
    """使用选择的方法去除所有水印区域，并可选地绘制红色框"""
    
    for area in WATERMARK_AREAS:
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]
        
        # 确保坐标在图像范围内
        x = max(0, min(x, frame.shape[1] - w))
        y = max(0, min(y, frame.shape[0] - h))
        w = min(w, frame.shape[1] - x)
        h = min(h, frame.shape[0] - y)
        
        # 根据选择的方法处理水印
        if REMOVAL_METHOD == "gaussian_blur":
            processed_roi = remove_watermark_gaussian_blur(frame, {"x": x, "y": y, "w": w, "h": h})
        elif REMOVAL_METHOD == "enhanced_blur":
            processed_roi = remove_watermark_enhanced_blur(frame, {"x": x, "y": y, "w": w, "h": h})
        elif REMOVAL_METHOD == "super_enhanced":
            processed_roi = remove_watermark_super_enhanced(frame, {"x": x, "y": y, "w": w, "h": h})
        elif REMOVAL_METHOD == "inpainting":
            processed_roi = remove_watermark_inpainting(frame, {"x": x, "y": y, "w": w, "h": h})
        elif REMOVAL_METHOD == "morphology":
            processed_roi = remove_watermark_morphology(frame, {"x": x, "y": y, "w": w, "h": h})
        else:
            processed_roi = remove_watermark_super_enhanced(frame, {"x": x, "y": y, "w": w, "h": h})
        
        # 应用处理后的区域
        frame[y:y+h, x:x+w] = processed_roi
        
        # 可选：绘制红色框
        if DRAW_WATERMARK_BOX:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    return frame

def process_video(input_path, output_folder):
    clip = VideoFileClip(input_path)
    # 模糊水印
    processed = clip.image_transform(remove_watermark)
    output_path = os.path.join(output_folder, "processed_" + os.path.basename(input_path))
    
    processed.write_videofile(output_path, codec='libx264', audio_codec='aac')
    clip.close()

# 批量处理
input_folder = "input_videos"
output_folder = "output_videos"
os.makedirs(output_folder, exist_ok=True)

print("正在处理视频，去除水印...")
print(f"当前配置了 {len(WATERMARK_AREAS)} 个水印区域:")
for i, area in enumerate(WATERMARK_AREAS):
    print(f"  水印{i+1}: {area['label']} - 坐标({area['x']}, {area['y']}) 大小({area['w']}x{area['h']})")
print(f"绘制红色框: {'开启' if DRAW_WATERMARK_BOX else '关闭'}")
print(f"去除方法: {REMOVAL_METHOD}")

# 可用的去除方法说明
print("\n可用的去除方法:")
print("  - gaussian_blur: 标准高斯模糊 (快速)")
print("  - enhanced_blur: 增强模糊 (效果较好)")
print("  - super_enhanced: 超级增强 (推荐，针对顽固水印)")
print("  - inpainting: 图像修复 (适合复杂水印)")
print("  - morphology: 形态学操作 (适合特定类型水印)")

for file in os.listdir(input_folder):
    if file.endswith((".mp4", ".mov")):
        print(f"处理文件: {file}")
        process_video(os.path.join(input_folder, file), output_folder)
