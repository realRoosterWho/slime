import cv2
import time

# 打开摄像头，通常 /dev/video0 是树莓派主摄像头
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("无法打开摄像头")
    exit()

print("摄像头打开成功，开始拍摄10张照片...")

for i in range(10):
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头帧")
        break
    
    # 保存图像到文件
    filename = f"camera_photo/photo_{i+1}.jpg"
    cv2.imwrite(filename, frame)
    print(f"已保存照片: {filename}")
    
    # 等待1秒
    time.sleep(1)

print("拍摄完成！")
cap.release()
cv2.destroyAllWindows()
