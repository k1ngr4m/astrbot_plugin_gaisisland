import time
from typing import Optional

from astrbot.api.event import filter, AstrMessageEvent
from ..models.user import User
from ...db.database import DatabaseManager
from ..dao.user_dao import UserDAO
from ...enums.msg_enum import MsgEnum


class UserService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.user_dao = UserDAO(db_manager)

    async def register_command(self, event: AstrMessageEvent):
        """用户注册命令"""
        user_id = event.get_sender_id()
        platform = event.get_platform_name() or "unknown"
        group_id = event.get_group_id() or ""
        nickname = event.get_sender_name() or f"用户{user_id[-4:]}"

        # 检查用户是否已存在
        if self.get_user(user_id):
            yield event.plain_result(MsgEnum.ALREADY_REGISTERED.value)
            return

        # 创建新用户
        user = self.create_user(user_id, platform, group_id, nickname)

        # 发送注册成功消息
        yield event.plain_result(MsgEnum.REGISTRATION_SUCCESS.value.format(nickname))

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        return self.user_dao.get_user_by_id(user_id)

    def create_user(self, user_id: str, platform: str, group_id: str, nickname: str) -> User:
        """创建新用户"""
        now = int(time.time())
        user = User(
            user_id=user_id,
            platform=platform,
            group_id=group_id,
            nickname=nickname,
            created_at=now,
            updated_at=now
        )

        self.user_dao.create_user(user)
        return user