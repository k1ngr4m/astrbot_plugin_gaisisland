from enum import Enum

class MsgEnum(Enum):
    """
    消息枚举类
    """
    # 用户相关
    ALREADY_REGISTERED = "该用户已注册"
    REGISTRATION_SUCCESS = "用户 {nickname} 注册成功"
