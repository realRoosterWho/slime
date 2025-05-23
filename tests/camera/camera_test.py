#!/usr/bin/python3
from picamera2 import Picamera2
import time

picam2 = Picamera2()
picam2.start()
time.sleep(2)  # 等待相机初始化

filename = "current_image.jpg"
picam2.capture_file(filename)
print(f"已拍摄照片: {filename}")

picam2.stop()
