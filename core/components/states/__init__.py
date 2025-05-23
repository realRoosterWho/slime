# 基础状态类
from .init_state import InitState
from .gen_slime_image_state import GenSlimeImageState
from .show_slime_image_state import ShowSlimeImageState
from .show_greeting_state import ShowGreetingState
from .ask_photo_state import AskPhotoState
from .take_photo_state import TakePhotoState
from .analyze_photo_state import AnalyzePhotoState
from .suggest_destination_state import SuggestDestinationState

# 奖励系统状态
from .wait_for_new_photo_state import WaitForNewPhotoState
from .take_new_photo_state import TakeNewPhotoState
from .analyze_new_photo_state import AnalyzeNewPhotoState
from .analyze_reward_state import AnalyzeRewardState
from .generate_reward_image_state import GenerateRewardImageState
from .show_reward_state import ShowRewardState

__all__ = [
    'InitState',
    'GenSlimeImageState', 
    'ShowSlimeImageState',
    'ShowGreetingState',
    'AskPhotoState',
    'TakePhotoState',
    'AnalyzePhotoState',
    'SuggestDestinationState',
    'WaitForNewPhotoState',
    'TakeNewPhotoState',
    'AnalyzeNewPhotoState',
    'AnalyzeRewardState',
    'GenerateRewardImageState',
    'ShowRewardState',
] 