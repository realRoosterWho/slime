import subprocess
import os
from picamera2 import Picamera2
import time

class CameraManager:
    def __init__(self):
        self.picam2 = Picamera2()
        
    def take_photo(self, filename="current_image.jpg", save_path=None):
        """拍摄照片并保存
        Args:
            filename: 文件名，默认为current_image.jpg
            save_path: 保存路径，如果为None则保存到当前目录
        """
        try:
            print("启动相机...")
            self.picam2.start()
            time.sleep(2)  # 等待相机初始化
            
            # 如果指定了保存路径，确保目录存在
            if save_path:
                os.makedirs(save_path, exist_ok=True)
                full_path = os.path.join(save_path, filename)
            else:
                full_path = filename
            
            print(f"正在拍摄照片: {full_path}")
            self.picam2.capture_file(full_path)
            print(f"照片已保存: {full_path}")
            
            self.picam2.stop()
            return full_path  # 返回完整路径
        except Exception as e:
            print(f"拍照失败: {e}")
            return None
        finally:
            try:
                self.picam2.stop()
            except:
                pass

def run_camera_test(save_path=None, filename="current_image.jpg"):
    """拍照函数 - 为了保持向后兼容性
    Args:
        save_path: 保存路径，如果为None则保存到当前目录
        filename: 文件名，默认为current_image.jpg
    """
    camera = CameraManager()
    return camera.take_photo(filename=filename, save_path=save_path)

if __name__ == "__main__":
    run_camera_test()