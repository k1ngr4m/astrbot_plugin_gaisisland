from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .db.database import DatabaseManager
from .core.services.user_service import UserService


class GaisislandPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context
        self.db_manager = DatabaseManager()
        self.user_service = UserService(self.db_manager)


    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logger.info("盖之岛插件已加载")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.info("盖之岛插件已卸载")

    @filter.command("冒险注册")
    async def register_command(self, event: AstrMessageEvent):
        async for result in self.user_service.register_command(event):
            yield result


