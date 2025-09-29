import sqlite3
import os
import time
from typing import Optional
from astrbot.api import logger

class DatabaseManager:
    def __init__(self, db_path: str = "data/gaisisland.db"):
        # 确保data目录存在
        data_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "data"
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        return conn

    def init_database(self):
        """初始化数据库表结构"""
        import os
        conn = self.get_connection()
        cursor = conn.cursor()
        logger.info("开始初始化数据库")

        # 使用相对路径找到SQL文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file_path = os.path.join(current_dir, "migrations", "001_init.sql")

        with open(sql_file_path, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())

        # 加载作物数据
        crop_data_path = os.path.join(current_dir, "data", "crop_data.sql")
        if os.path.exists(crop_data_path):
            with open(crop_data_path, "r", encoding="utf-8") as f:
                cursor.executescript(f.read())

        conn.commit()
        cursor.close()
        logger.info("数据库初始化完成")

    def execute_query(self, query: str, params: tuple = ()):
        """执行查询操作（SELECT）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def execute_update(self, query: str, params: tuple = ()):
        """执行更新操作（INSERT/UPDATE/DELETE）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        conn.commit()
        conn.close()
        return rowcount

    def fetch_one(self, query: str, params: tuple = ()):
        """获取单条记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result

    def fetch_all(self, query: str, params: tuple = ()):
        """获取所有记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results