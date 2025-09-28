from typing import Optional

from ..models.player import Player
from ..db.database import DatabaseManager

class PlayerDAO:
    """用户数据访问对象，封装所有用户相关的数据库操作"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_player_by_id(self, user_id: str) -> Optional[Player]:
        """根据用户ID获取用户信息"""
        result = self.db.execute_query(
            "SELECT * FROM players WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return Player(*result[0])
        return None

    def create_player(self, player: Player) -> bool:
        """创建新用户"""
        try:
            self.db.execute_query(
                """INSERT INTO players (user_id, platform, group_id, nickname, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (player.user_id, player.platform, player.group_id, player.nickname, player.created_at, player.updated_at)
            )
            return True
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False
