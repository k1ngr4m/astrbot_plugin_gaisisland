import time
from typing import Optional

from astrbot.api.event import filter, AstrMessageEvent
from ..models.player import Player
from ..db.database import DatabaseManager
from ..dao.player_dao import PlayerDAO
from ..dao.farm_dao import FarmDAO
from ...enums.msg_enum import MsgEnum


class PlayerService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.player_dao = PlayerDAO(db_manager)
        self.farm_dao = FarmDAO(db_manager)

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
        player = self.create_player(user_id, platform, group_id, nickname)

        # 如果是在群聊中，检查是否需要创建农场
        if group_id:
            # 检查该群是否已有农场
            farm = self.farm_dao.get_farm_by_group_id(group_id)

            if not farm:
                # 创建新农场
                import time
                now = int(time.time())
                farm_name = f"{nickname}的农场"
                self.farm_dao.create_farm(group_id, farm_name, now, now)

                # 创建初始地块
                farm = self.farm_dao.get_farm_by_group_id(group_id)
                if farm:
                    self.farm_dao.create_plot(farm['id'], 0, now, now)

        # 发送注册成功消息
        yield event.plain_result(MsgEnum.REGISTRATION_SUCCESS.value.format(nickname=nickname))

    def get_user(self, user_id: str) -> Optional[Player]:
        """获取用户信息"""
        return self.player_dao.get_player_by_id(user_id)

    def create_player(self, user_id: str, platform: str, group_id: str, nickname: str) -> Player:
        """创建新用户"""
        now = int(time.time())
        player = Player(
            user_id=user_id,
            platform=platform,
            group_id=group_id,
            nickname=nickname,
            created_at=now,
            updated_at=now
        )

        self.player_dao.create_player(player)
        return player
