from enum import Enum, auto

class DeriveState(Enum):
    """漂流状态枚举"""
    VOICE_INPUT_MOOD = auto()      # 语音输入心情 (新增)
    PROCESS_MOOD = auto()          # 处理心情 (新增)
    INIT = auto()                  # 初始化
    GEN_SLIME_IMAGE = auto()       # 生成史莱姆图片
    SHOW_SLIME_IMAGE = auto()      # 显示史莱姆图片
    SHOW_GREETING = auto()         # 显示打招呼
    ASK_PHOTO = auto()             # 询问拍照
    TAKE_PHOTO = auto()            # 拍照
    ANALYZE_PHOTO = auto()         # 分析照片
    SUGGEST_DESTINATION = auto()   # 建议目的地
    WAIT_FOR_NEW_PHOTO = auto()    # 等待新的照片
    TAKE_NEW_PHOTO = auto()        # 拍摄新的照片
    ANALYZE_NEW_PHOTO = auto()     # 分析新的照片
    ANALYZE_REWARD = auto()        # 分析奖励
    GENERATE_REWARD_IMAGE = auto() # 生成奖励图片
    SHOW_REWARD = auto()           # 显示奖励
    GENERATE_FEEDBACK = auto()     # 生成反馈
    SHOW_FEEDBACK = auto()         # 显示反馈
    ASK_CONTINUE = auto()          # 询问是否继续
    SUMMARY = auto()               # 总结
    CLEANUP = auto()               # 清理
    EXIT = auto()                  # 退出 