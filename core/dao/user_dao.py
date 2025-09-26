from typing import Optional

from ..models.user import User
from ...db.database import DatabaseManager

class UserDAO:
    """用户数据访问对象，封装所有用户相关的数据库操作"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户信息"""
        result = self.db.execute_query(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return User(*result[0])
        return None

    def create_user(self, user: User) -> bool:
        """创建新用户"""
        try:
            self.db.execute_query(
                """INSERT INTO users (user_id, platform, group_id, nickname, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user.user_id, user.platform, user.group_id, user.nickname, user.created_at, user.updated_at)
            )
            return True
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False
