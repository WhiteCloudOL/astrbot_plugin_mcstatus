from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, StarTools, register
from astrbot.core.platform.message_type import MessageType
from .core.data_manager import DataManager
from .core.draw import Draw
from .core.command_func import CommandFunc
import os

plugin_version = "1.0.6"

@register("mcstatus", "WhiteCloudCN", "一个获取MC服务器状态的插件", plugin_version)
class mcstatus(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config # 插件配置
        plugin_data_dir = StarTools.get_data_dir("mcstatus")
        self.bot_config = context.get_config() # 机器人配置
        self.admin_list = self.bot_config["admins_id"] # 机器人管理员列表
        self.draw_output_path=os.path.join(plugin_data_dir,'draw_temp.png')
        
        self.datamanager = DataManager(config_file=plugin_data_dir / "mcstatus.json")
        self.datamanager.load_config()

        self.commandFunc = CommandFunc(admin_list=self.admin_list,
                                       datamanager=self.datamanager,
                                       plugin_version=plugin_version,
                                       config=self.config)

    def enabled_group_check(self, event: AstrMessageEvent) -> bool:
        """权限检查，私聊跳过"""
        group_id = event.get_group_id()
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

    @filter.command("mcstatus",alias=["mc状态","MC状态","mcs"])
    async def mcstatus(self,
                       event: AstrMessageEvent,
                       subcommand: str = None,
                       command_text_a: str = None,
                       command_text_b: str = None):
        """
        插件主函数,/mcstatus help获取帮助
        """
        if not self.enabled_group_check(event):
            return
        match subcommand:
            case None:
                yield event.plain_result("❌缺少参数，请输入/mcstatus help查询用法")
            case "motd":
                yield await self.commandFunc._handle_motd(event=event,
                                                          server_addr=command_text_a)
            case "add":
                yield await self.commandFunc._handle_add(event=event,
                                                         server_name=command_text_a,
                                                         server_addr=command_text_b)
            case "players":
                yield await self.commandFunc._handle_players(event=event,
                                                             server_addr=command_text_a)
            case "del":
                yield await self.commandFunc._handle_del(event=event,
                                                         server_name=command_text_a)
            case "look":
                yield await self.commandFunc._handle_look(event=event,
                                                          server_name=command_text_a)
            case "set":
                yield await self.commandFunc._handle_set(event=event,
                                                         server_name=command_text_a,
                                                         server_addr=command_text_b)
            case "list":
                yield await self.commandFunc._handle_list(event=event)
            case "clear":
                yield await self.commandFunc._handle_clear(event=event)
            case "help":
                yield await self.commandFunc._handle_help(event=event,
                                                          draw_output_path=self.draw_output_path)
            case _:
                yield event.plain_result("❌无相关指令，请输入/mcstatus help查询用法")

    # @filter.command("draw")
    # async def draw(self, event: AstrMessageEvent):
    #     """
    #     绘图命令（测试）
    #     """
    #     messages = event.message_str.split(' ',1)
    #     if len(messages)<2:
    #         final_text = "AstrBot Plugin@清蒸云鸭\n未检测到输入字符串！"
    #     else:
    #         final_text = messages[1].strip()
    #         if final_text == "":
    #             final_text = "AstrBot Plugin@清蒸云鸭\n未检测到输入字符串！"
    #     logger.info(f"生成文本图片：{final_text}")
    #     final_text = self.commandFunc.auto_wrap_text(final_text,20)
    #     line_count = final_text.count('\n')
    #     if line_count==0:
    #         line_count+=1
    #     drawing = Draw(output=self.draw_output_path)
    #     success, result_path_or_error = await drawing.create_image_with_text(text=final_text,seted_font=self.config["font"],font_size=60,target_size=(1200,100+60*line_count))
    #     if success:
    #         yield event.image_result(result_path_or_error)
    #     else:
    #         yield event.plain_result(result_path_or_error)

    
    async def terminate(self):
        if self.datamanager.save_config():
            logger.info("数据保存成功，已卸载插件！")
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''