import subprocess
import os
from picamera2 import Picamera2
import time

class CameraManager:
    def __init__(self):
        self.picam2 = Picamera2()
        self.is_started = False
        
    def start_camera(self):
        """预先启动相机"""
        if not self.is_started:
            try:
                print("启动相机...")
                self.picam2.start()
                time.sleep(2)  # 等待相机初始化
                self.is_started = True
                print("相机已启动并准备就绪")
            except Exception as e:
                print(f"启动相机失败: {e}")
                self.is_started = False
    
    def stop_camera(self):
        """停止相机"""
        if self.is_started:
            try:
                self.picam2.stop()
                self.is_started = False
                print("相机已停止")
            except Exception:
                pass
        
    def take_photo(self, filename="current_image.jpg"):
        """拍摄照片并保存（快速拍照）"""
        try:
            # 如果相机没有启动，先启动它
            if not self.is_started:
                self.start_camera()
            
            if self.is_started:
                print(f"正在拍摄照片: {filename}")
                self.picam2.capture_file(filename)
                print(f"照片已保存: {filename}")
                return True
            else:
                print("相机未启动，拍照失败")
                return False
                
        except Exception as e:
            print(f"拍照失败: {e}")
            return False
    
    def __del__(self):
        """析构函数，确保相机被正确关闭"""
        self.stop_camera()

def run_camera_test():
    """拍照函数 - 为了保持向后兼容性"""
    camera = CameraManager()
    result = camera.take_photo()
    camera.stop_camera()  # 单次使用后停止相机
    return result

if __name__ == "__main__":
    run_camera_test()