from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger, AstrBotConfig
from mcstatus import JavaServer
from mcstatus.status_response import JavaStatusResponse
from .data_manager import DataManager
from .draw import Draw

class CommandFunc:
    def __init__(self,admin_list: list,datamanager: DataManager,plugin_version: str,config: AstrBotConfig):
        self.admin_list = admin_list
        self.datamanager = datamanager
        self.plugin_version = plugin_version
        self.config = config
        pass



    async def _lookup_server(self, server_addr: str):
        """查询服务器信息"""
        try:
            server = await JavaServer.async_lookup(server_addr)
            status = await server.async_status()
            return server, status
        except Exception as e:
            logger.error(f"查询服务器信息失败, 原因: {str(e)}")
            return None, None

    async def get_server_status(self, server_addr: str):
        try:
            server_addr = server_addr.strip()
        except Exception as e:
            logger.error(f"服务器地址格式错误, 原因: {str(e)}")  # 修正了拼写错误
            return None
        
        try:
            # 尝试直接解析（含SRV）
            server, status = await self._lookup_server(server_addr)
            if status is None:
                if ":" not in server_addr:
                    # 尝试默认端口25565
                    server_addr = f"{server_addr}:25565"
                server, status = await self._lookup_server(server_addr)
                if status is None:
                    return None
            if hasattr(status.description, 'to_plain'):
                motd = status.description.to_plain()
            elif hasattr(status.description, 'to_minecraft'):
                motd = status.description.to_minecraft()
            else:
                motd = str(status.description)

            # TODO 添加颜色
            import re
            motd = re.sub(r'§[0-9a-fk-or]', '', motd)

            players_list = []
            if status.players.sample is not None:
                players_list = [player.name for player in status.players.sample]

            return {
                'server_addr': server_addr,
                'online': status.players.online,
                'max': status.players.max,
                'latency': round(status.latency, 2),
                'motd': motd,
                'version': status.version.name,
                'players': players_list
            }
        except Exception as e:
            logger.error(f"获取服务器状态出错, 原因: {str(e)}")
            return None


    def tras_players_to_string(self, players: list) -> str:
        if not players:
            return "无"
        if len(players) > 20:
            players = players[:20] + ["...等更多"]
        res = ""
        for i in range(1,len(players)):
            res += f"{players[i-1]}, "
        res += f"{players[-1]}"
        return res


    def to_string(self, server_status: dict) -> str:
        """
        格式化的状态字符串，如果状态数据为None则返回错误信息
        """
        if server_status is None:
            return (f"❌ 无法获取服务器的状态\n"
                    "请检查：\n"
                    "1. 服务器地址是否正确\n"
                    "2. 服务器是否在线\n"
                    "3. 端口是否正确（默认25565）")
        
        players_list = self.tras_players_to_string(server_status['players'])

        return (
            f"✅ 服务器【{server_status['server_addr']}】状态：\n"
                f"📋 版本: {server_status['version']}\n"
                f"👥 玩家: {server_status['online']}/{server_status['max']}\n"
                f"📋 在线玩家：{players_list}\n"
                f"📶 延迟: {server_status['latency']}ms\n"
                f"📝 MOTD: {server_status['motd']}"
        )
    

    def players_to_string(self, server_status: dict) -> str:
        """
        格式化的玩家列表字符串
        """
        if server_status is None:
            return (f"❌ 无法获取服务器的玩家列表\n"
                    "请检查：\n"
                    "1. 服务器地址是否正确\n"
                    "2. 服务器是否在线\n"
                    "3. 端口是否正确（默认25565）")
        
        if not server_status['players']:
            return (f"🟢 服务器【{server_status['server_addr']}】在线玩家：\n"
                    f"👥 玩家: {server_status['online']}/{server_status['max']}\n"
                    "📝 当前没有在线玩家或玩家列表不可见")
        
        players_list = self.tras_players_to_string(server_status['players'])

        return (f"🟢 服务器【{server_status['server_addr']}】在线玩家：\n"
                f"👥 玩家: {server_status['online']}/{server_status['max']}\n"
                f"📋 玩家列表：\n{players_list}")
    
    @staticmethod
    def auto_wrap_text(text, max_chars_per_line, keep_original_newlines=True):
        """
        自动换行函数，处理字符串中的普通\n字符并按指定字符数换行
        
        Args:
            text: 输入字符串（可能包含普通的\n字符）
            max_chars_per_line: 每行最大字符数
            keep_original_newlines: 是否保留原有的\n换行符
        
        Returns:
            处理后的字符串
        """
        if not text or max_chars_per_line <= 0:
            return text
        
        result_lines = []
        
        if keep_original_newlines:
            segments = []
            current_segment = ""
            i = 0
            
            while i < len(text):
                if i < len(text) - 1 and text[i] == '\\' and text[i+1] == 'n':
                    if current_segment:
                        segments.append(current_segment)
                        current_segment = ""
                    segments.append("\n")
                    i += 2
                else:
                    current_segment += text[i]
                    i += 1
            
            if current_segment:
                segments.append(current_segment)
            
            current_paragraph = ""
            for segment in segments:
                if segment == "\n":
                    if current_paragraph:
                        lines = []
                        current_line = ""
                        for char in current_paragraph:
                            if len(current_line) + 1 > max_chars_per_line:
                                if current_line:
                                    lines.append(current_line)
                                current_line = char
                            else:
                                current_line += char
                        if current_line:
                            lines.append(current_line)
                        result_lines.extend(lines)
                        current_paragraph = ""
                    result_lines.append("")
                else:
                    current_paragraph += segment
            
            if current_paragraph:
                lines = []
                current_line = ""
                for char in current_paragraph:
                    if len(current_line) + 1 > max_chars_per_line:
                        if current_line:
                            lines.append(current_line)
                        current_line = char
                    else:
                        current_line += char
                if current_line:
                    lines.append(current_line)
                result_lines.extend(lines)
        
        else:
            processed_text = ""
            i = 0
            while i < len(text):
                if i < len(text) - 1 and text[i] == '\\' and text[i+1] == 'n':
                    processed_text += " "
                    i += 2
                else:
                    processed_text += text[i]
                    i += 1
            
            lines = []
            current_line = ""
            for char in processed_text:
                if len(current_line) + 1 > max_chars_per_line:
                    if current_line:
                        lines.append(current_line)
                    current_line = char
                else:
                    current_line += char
            
            if current_line:
                lines.append(current_line)
            
            result_lines = lines
        
        return '\n'.join(result_lines)

    async def _handle_motd(self, event: AstrMessageEvent, server_addr: str):
        """
        Command: /mcstatus motd
        Usage: 获取JE服务器MOTD
        """
        if server_addr is None:
            return event.plain_result("❌格式错误！正确用法：/mcstatus motd 服务器地址")
        else:
            server_status = await self.get_server_status(server_addr)
            return event.plain_result(self.to_string(server_status))

    async def _handle_players(self, event: AstrMessageEvent, server_addr: str = None):
        """
        Command: /mcstatus players
        Usage: 获取JE服务器在线玩家列表
        """
        if server_addr is None:
            return event.plain_result("❌格式错误！正确用法：/mcstatus players 服务器地址")
        else:
            server_status = await self.get_server_status(server_addr)
            return event.plain_result(self.players_to_string(server_status))

    async def _handle_add(self,
                          event: AstrMessageEvent,
                          server_name: str,
                          server_addr: str):
        """
        Command: /mcstatus add
        Usage: 添加服务器
        """
        if server_name is None or server_addr is None:
            return event.plain_result("❌格式错误！正确用法：/mcstatus add [服务器名(任意)] [服务器地址]")
            return
        else:
            if self.datamanager.add_server_addr(server_name,server_addr):
                return event.plain_result(f"✅服务器{server_name} 添加成功！")
            else:
                return event.plain_result("❌添加失败，发生内部错误")

    async def _handle_del(self,
                          event: AstrMessageEvent,
                          server_name: str):
        if server_name is None:
            return event.plain_result("❌格式错误！正确用法：/mcstatus del [服务器名]")
        else:
            if self.datamanager.remove_server_addr(server_name):
                return event.plain_result(f"✅服务器{server_name} 删除成功！")
            else:
                return event.plain_result("❌删除失败，发生内部错误")

    async def _handle_look(self,
                           event: AstrMessageEvent,
                           server_name: str):
        if server_name is None:
            return event.plain_result("❌格式错误！正确用法：/mcstatus look [服务器名]") 
        else:
            server_status = await self.get_server_status(self.datamanager.get_server_addr(server_name))
            data = self.to_string(server_status)
            if data is not None:
                return event.plain_result(data)
            else:
                return event.plain_result("❌未找到服务器，请检查服务器地址")

    async def _handle_set(self,
                          event: AstrMessageEvent,
                          server_name: str,
                          server_addr: str):
        if server_name is None or server_addr is None:
            return event.plain_result("❌格式错误！正确用法：/mcstatus set [服务器名] [新服务器地址]")
        else:
            if self.datamanager.update_server_addr(server_name, server_addr):
                return event.plain_result(f"{server_name}更新成功，新地址为{server_addr}")
            else:
                return event.plain_result(f"❌{server_name}更新失败，请检查：\n"
                                         f"1.名称是否存在\n"
                                         f"2.地址是否合法")
    async def _handle_list(self,event: AstrMessageEvent):
        data = self.datamanager.get_all_configs()
        if data is not None:
            result = "✅已存储服务器：\n"
            cnt = 1
            for key in data:
                result+=f"{cnt}.{key}: {data[key]}\n"
                cnt += 1
            return event.plain_result(result)
        else:
            return event.plain_result("🐸暂无存储服务器，请用/mcstatus add添加")
    
    async def _handle_clear(self,event: AstrMessageEvent):
        self.admin_list = self.bot_config["admins_id"]
        if event.get_sender_id() not in self.admin_list:
            return event.plain_result(f"❌清空失败，杂鱼{event.get_sender_name()}(id:{event.get_sender_id()}) 的权限不足还妄想清空呢~")
        if self.datamanager.clear_all_configs():
            return event.plain_result("✅清空成功")
        else:
            return event.plain_result("❌清空失败，请重试或手动清理")

    async def _handle_help(self,
                           event: AstrMessageEvent,
                           draw_output_path: str):
        drawing = Draw(output=draw_output_path)
        success, result_path_or_error = await drawing.create_image_with_text(
            text=f"💕MCStatus 插件帮助[v{self.plugin_version}]\n"
                  "/mcstatus\n"
                  " ├─ help  ->获取帮助\n"
                  " ├─ motd  ->获取服务器MOTD状态信息\n"
                  " ├─ players [服务器地址] -> 获取在线玩家列表\n"
                  " ├─ add [名称] [服务器地址] -> 存储新服务器\n"
                  " ├─ del [名称]  -> 删除服务器\n" 
                  " ├─ look [名称] ->查询服务器名称对应的服务器信息\n"
                  " ├─ list  ->显示所有已存储服务器，默认显示第一页\n"
                  " └─ clear ->删除所有存储服务器 *管理员命令\n",
                  #"/draw [text] -> 绘制文本",
            font_size=90,
            target_size=(1200,620))
        if success:
            return event.image_result(result_path_or_error)
        else:
            return event.plain_result(result_path_or_error)