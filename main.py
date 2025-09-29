from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .core.db.database import DatabaseManager
from .core.services.player_service import PlayerService
from .core.services.farm_service import FarmService


class GaisislandPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context
        self.db_manager = DatabaseManager()
        self.player_service = PlayerService(self.db_manager)
        self.farm_service = FarmService(self.db_manager)


    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logger.info("盖之岛插件已加载")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.info("盖之岛插件已卸载")

    @filter.command("注册")
    async def register_command(self, event: AstrMessageEvent):
        async for result in self.player_service.register_command(event):
            yield result

    @filter.command("种植")
    async def plant_command(self, event: AstrMessageEvent):
        # 解析命令参数
        message = event.get_message_str()
        args = message.split()[1:] if len(message.split()) > 1 else []

        if len(args) < 2:
            yield event.plain_result("用法: /种植 <地块编号> <作物名称>")
            return

        try:
            plot_index = int(args[0])
            crop_key = args[1]
        except ValueError:
            yield event.plain_result("地块编号必须是数字")
            return

        async for result in self.farm_service.plant_command(event, plot_index, crop_key):
            yield result

    @filter.command("收获")
    async def harvest_command(self, event: AstrMessageEvent):
        # 解析命令参数
        message = event.get_message_str()
        args = message.split()[1:] if len(message.split()) > 1 else []

        if len(args) < 1:
            yield event.plain_result("用法: /收获 <地块编号>")
            return

        try:
            plot_index = int(args[0])
        except ValueError:
            yield event.plain_result("地块编号必须是数字")
            return

        async for result in self.farm_service.harvest_command(event, plot_index):
            yield result

    @filter.command("状态")
    async def status_command(self, event: AstrMessageEvent):
        # 解析命令参数
        message = event.get_message_str()
        args = message.split()[1:] if len(message.split()) > 1 else []

        if len(args) < 1:
            yield event.plain_result("用法: /状态 <地块编号>")
            return

        try:
            plot_index = int(args[0])
        except ValueError:
            yield event.plain_result("地块编号必须是数字")
            return

        async for result in self.farm_service.status_command(event, plot_index):
            yield result


