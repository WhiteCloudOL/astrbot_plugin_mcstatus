
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.platform.message_type import MessageType

from .core.command_func import CommandFunc
from .core.data_manager import DataManager

plugin_version = "2.0.3"

class mcstatus(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        plugin_data_dir = StarTools.get_data_dir("mcstatus")
        self.bot_config = context.get_config()
        self.admin_list = self.bot_config["admins_id"]

        self.datamanager = DataManager(config_file=plugin_data_dir / "mcstatus.json")
        self.datamanager.load_config()

        self.commandFunc = CommandFunc(admin_list=self.admin_list,
                                       datamanager=self.datamanager,
                                       plugin_version=plugin_version,
                                       config=self.config,
                                       plugin_data_dir=str(plugin_data_dir))

    def enabled_group_check(self, event: AstrMessageEvent) -> bool:
        """权限检查，私聊跳过"""
        group_id = event.get_group_id()
        if not group_id: # 私聊
             return True

        mode = self.config["divide_group"]["block_method"]
        group_list = self.config["divide_group"].get("control_list",[])

        if event.get_message_type() != MessageType.GROUP_MESSAGE:
            return True
        if mode == "blacklist":
            if group_id in group_list:
                return False
            return True
        elif mode == "whitelist":
            if group_id in group_list:
                return True
            return False
        return False

    @filter.command("mcstatus", alias={"mc状态","MC状态","mcs"})
    async def mcstatus(self,
                       event: AstrMessageEvent,
                       subcommand: str = "",
                       command_text_a: str = "",
                       command_text_b: str = ""):
        """
        插件主函数,/mcstatus help获取帮助
        """
        if not self.enabled_group_check(event):
            return

        # 初始化返回结果变量
        result_tuple: tuple[bool, str] = (False, "")

        match subcommand:
            case "":
                 result_tuple = (False, "❌缺少参数，请输入/mcstatus help查询用法")
            case "motd":
                 result_tuple = await self.commandFunc._handle_motd(event=event, server_addr=command_text_a)
            case "add":
                 result_tuple = await self.commandFunc._handle_add(event=event, server_name=command_text_a, server_addr=command_text_b)
            case "players":
                 result_tuple = await self.commandFunc._handle_players(event=event, server_addr=command_text_a)
            case "del":
                 result_tuple = await self.commandFunc._handle_del(event=event, server_name=command_text_a)
            case "look":
                 result_tuple = await self.commandFunc._handle_look(event=event, server_name=command_text_a)
            case "set":
                 result_tuple = await self.commandFunc._handle_set(event=event, server_name=command_text_a, server_addr=command_text_b)
            case "list":
                 result_tuple = await self.commandFunc._handle_list(event=event)
            case "clear":
                 result_tuple = await self.commandFunc._handle_clear(event=event)
            case "help":
                 result_tuple = await self.commandFunc._handle_help(event=event)
            case _:
                 result_tuple = (False, "❌无相关指令，请输入/mcstatus help查询用法")

        # 根据返回的 tuple 判断发送图片还是文本
        is_image, data = result_tuple
        if is_image:
            yield event.image_result(data)
        else:
            yield event.plain_result(data)

    async def terminate(self):
        if self.datamanager.save_config():
            logger.info("数据保存成功，已卸载插件！")
