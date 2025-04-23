from picamera2 import Picamera2
import cv2
import time

# 初始化摄像头
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)  # 等待摄像头启动

print("摄像头打开成功，开始拍摄10张照片...")

for i in range(10):
    # 捕获图像
    frame = picam2.capture_array()
    
    # 保存图像到文件
    filename = f"camera_photo/photo_{i+1}.jpg"
    cv2.imwrite(filename, frame)
    print(f"已保存照片: {filename}")
    
    # 等待1秒
    time.sleep(1)

print("拍摄完成！")
picam2.stop()
cv2.destroyAllWindows()
