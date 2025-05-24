import subprocess
import os
from picamera2 import Picamera2
import time

class CameraManager:
    def __init__(self):
        self.picam2 = Picamera2()
        
    def take_photo(self, filename="current_image.jpg"):
        """拍摄照片并保存"""
        try:
            print("启动相机...")
            self.picam2.start()
            time.sleep(2)  # 等待相机初始化
            
            print(f"正在拍摄照片: {filename}")
            self.picam2.capture_file(filename)
            print(f"照片已保存: {filename}")
            
            self.picam2.stop()
            return True
        except Exception as e:
            print(f"拍照失败: {e}")
            return False
        finally:
            try:
                self.picam2.stop()
            except:
                pass

def run_camera_test():
    """拍照函数 - 为了保持向后兼容性"""
    camera = CameraManager()
    return camera.take_photo()

if __name__ == "__main__":
    run_camera_test()