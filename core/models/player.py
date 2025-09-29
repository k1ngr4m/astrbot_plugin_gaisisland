import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    """用户实体类"""
    user_id: str
    platform: str = "unknown"  # 平台 (qq, dingtalk, feishu等)
    group_id: str = ""  # 群组ID
    nickname: str = ""
    gold: int = 20000  # 金币
    exp: int = 0     # 经验值
    level: int = 1   # 等级
    id: Optional[int] = None  # 数据库ID
    created_at: int = field(default_factory=lambda: int(time.time()))
    updated_at: int = field(default_factory=lambda: int(time.time()))