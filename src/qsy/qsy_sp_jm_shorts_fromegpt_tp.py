from moviepy import VideoFileClip
import cv2
import os
import numpy as np

# 定义多个水印区域 - 你可以在这里添加更多水印坐标
WATERMARK_AREAS = [
    {"x": 14, "y": 14, "w": 136, "h": 64, "label": "WATERMARK1"},  # 第一个水印
    {"x": 674, "y": 1062, "w": 146, "h": 48, "label": "WATERMARK2"},  # 第二个水印 - 请根据实际情况修改坐标
    # 如果需要更多水印，可以继续添加
    # {"x": 500, "y": 300, "w": 150, "h": 40, "label": "WATERMARK3"},
]

def remove_watermark(get_frame, t):
    """处理视频帧，去除水印"""
    frame = get_frame(t)
    frame = frame.copy()
    
    # 模糊所有水印区域
    for area in WATERMARK_AREAS:
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]
        
        # 确保坐标在有效范围内
        if x >= 0 and y >= 0 and x + w <= frame.shape[1] and y + h <= frame.shape[0]:
            roi = frame[y:y+h, x:x+w]
            if roi.size > 0:  # 确保ROI不为空
                blurred = cv2.GaussianBlur(roi, (51, 51), 0)  # 高斯模糊
                frame[y:y+h, x:x+w] = blurred
    
    return frame

def process_video(input_path, output_folder):
    try:
        clip = VideoFileClip(input_path)
        
        # 使用 transform 方法
        processed = clip.transform(remove_watermark)
        
        output_path = os.path.join(output_folder, "processed_" + os.path.basename(input_path))
        
        # 写入视频文件
        processed.write_videofile(
            output_path, 
            codec='libx264', 
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # 清理资源
        clip.close()
        processed.close()
        
        print(f"✅ 成功处理: {os.path.basename(input_path)}")
        
    except Exception as e:
        print(f"❌ 处理失败 {os.path.basename(input_path)}: {str(e)}")
        if 'clip' in locals():
            clip.close()

# 批量处理
input_folder = "input_videos"
output_folder = "output_videos"
os.makedirs(output_folder, exist_ok=True)

print("正在处理视频，去除水印...")
print(f"当前配置了 {len(WATERMARK_AREAS)} 个水印区域:")
for i, area in enumerate(WATERMARK_AREAS):
    print(f"  水印{i+1}: {area['label']} - 坐标({area['x']}, {area['y']}) 大小({area['w']}x{area['h']})")

# 检查输入文件夹是否存在
if not os.path.exists(input_folder):
    print(f"❌ 输入文件夹不存在: {input_folder}")
    exit(1)

# 获取视频文件列表
video_files = [f for f in os.listdir(input_folder) if f.endswith((".mp4", ".mov", ".avi", ".mkv"))]

if not video_files:
    print(f"❌ 在 {input_folder} 文件夹中没有找到视频文件")
    exit(1)

print(f"找到 {len(video_files)} 个视频文件")

for file in video_files:
    print(f"处理文件: {file}")
    process_video(os.path.join(input_folder, file), output_folder)

print("🎉 所有视频处理完成！")
