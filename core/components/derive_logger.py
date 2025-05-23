import os
import json
import shutil
from datetime import datetime

class DeriveLogger:
    def __init__(self):
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(project_root, "derives", self.timestamp)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_data = {
            "timestamp": self.timestamp,
            "steps": [],
            "images": {},
            "prompts": {},
            "responses": {}
        }
    
    def log_step(self, step_name, message):
        """记录步骤信息并立即保存日志"""
        print(f"\n📝 {message}")
        self.log_data["steps"].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "step": step_name,
            "message": message
        })
        # 每记录一步就立即保存日志，防止断电丢失数据
        self.save_log()
        
    def save_image(self, image_path, image_type):
        """保存图片到日志目录"""
        if os.path.exists(image_path):
            filename = os.path.basename(image_path)
            new_path = os.path.join(self.log_dir, filename)
            shutil.copy2(image_path, new_path)
            self.log_data["images"][image_type] = filename
            # 每保存一张图片就立即保存日志
            self.save_log()
            return new_path
        return None
    
    def log_prompt(self, prompt_type, prompt):
        """记录提示词并立即保存日志"""
        self.log_data["prompts"][prompt_type] = prompt
        self.save_log()
    
    def log_response(self, response_type, response):
        """记录响应并立即保存日志"""
        self.log_data["responses"][response_type] = response
        self.save_log()
    
    def save_log(self):
        """保存日志文件"""
        try:
            log_path = os.path.join(self.log_dir, "derive_log.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(self.log_data, f, ensure_ascii=False, indent=2)
            # print(f"✅ 日志已保存到: {log_path}")  # 注释掉频繁的输出
        except Exception as e:
            print(f"⚠️ 保存日志时出错: {e}")

    def get_timestamped_filename(self, original_name, ext):
        """生成带时间戳的文件名"""
        base_name = os.path.splitext(original_name)[0]
        return f"{base_name}_{self.timestamp}{ext}" 