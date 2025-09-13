from moviepy import VideoFileClip
import cv2
import os

# 定义多个水印区域 - 你可以在这里添加更多水印坐标
WATERMARK_AREAS = [
    {"x": 1200, "y": 660, "w": 50, "h": 36, "label": "WATERMARK1"},  # 第一个水印
    # 如果需要更多水印，可以继续添加
    # {"x": 500, "y": 300, "w": 150, "h": 40, "label": "WATERMARK3"},
]

# 是否在水印区域画红色框（True 开启 / False 关闭）
DRAW_WATERMARK_BOX = False

def remove_watermark(frame):
    frame = frame.copy()
    """模糊所有水印区域，并可选地绘制红色框"""
    for area in WATERMARK_AREAS:
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]
        roi = frame[y:y+h, x:x+w]
        blurred = cv2.GaussianBlur(roi, (51, 51), 0)  # 高斯模糊
        frame[y:y+h, x:x+w] = blurred
        if DRAW_WATERMARK_BOX:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)  # 红色框
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

for file in os.listdir(input_folder):
    if file.endswith((".mp4", ".mov")):
        print(f"处理文件: {file}")
        process_video(os.path.join(input_folder, file), output_folder)
