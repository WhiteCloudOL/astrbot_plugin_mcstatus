import glob
import os
import time
import uuid

from mcstatus import JavaServer

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent

from .data_manager import DataManager
from .draw import Draw


class CommandFunc:
    def __init__(self, admin_list: list, datamanager: DataManager, plugin_version: str, config: AstrBotConfig, plugin_data_dir: str):
        self.admin_list = admin_list
        self.datamanager = datamanager
        self.plugin_version = plugin_version
        self.config = config
        self.plugin_data_dir = plugin_data_dir

        self.images_dir = os.path.join(plugin_data_dir, "data")
        os.makedirs(self.images_dir, exist_ok=True)

        bg_name = config.get("bg", "bg.jpg")
        if isinstance(bg_name, dict):
            bg_name = "bg.jpg"

        self.bg_name = str(bg_name)

    def _get_new_image_path(self) -> str:
        """生成新的图片路径并清理旧缓存"""
        max_temp = self.config.get("max_temp", 5)

        # 清理旧缓存
        existing_images = glob.glob(os.path.join(self.images_dir, "*.png"))
        if len(existing_images) >= max_temp:
            # 按修改时间排序，最旧的在前面
            existing_images.sort(key=os.path.getmtime)
            # 删除多余的图片
            for img_to_del in existing_images[:len(existing_images) - max_temp + 1]:
                try:
                    os.remove(img_to_del)
                except Exception as e:
                    logger.error(f"清理缓存图片失败: {e}")

        # 生成新路径
        new_filename = f"mcstatus_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
        return os.path.join(self.images_dir, new_filename)

    @property
    def is_global(self) -> bool:
        divide_group = self.config.get("divide_group", {})
        return not divide_group.get("divide_data", False)

    async def _lookup_server(self, server_addr: str):
        """
        尝试查询服务器信息，支持自动重试和超时处理
        """
        try:
            server = await JavaServer.async_lookup(server_addr)
            status = await server.async_status()
            return server, status
        except Exception as e:
            error_msg = str(e)
            if "Socket did not respond" in error_msg or "WinError 64" in error_msg:
                logger.warning(f"服务器 {server_addr} 响应超时或连接中断")
            else:
                logger.error(f"查询服务器 {server_addr} 失败: {error_msg}")
            return None, None

    async def get_server_status(self, server_addr: str) -> dict | None:
        try:
            if not server_addr:
                return None
            server_addr = server_addr.strip()
        except Exception:
            return None

        try:
            # 第一次尝试：原始地址
            server, status = await self._lookup_server(server_addr)

            # 第二次尝试：如果失败且没有端口，补全默认端口 25565
            if status is None and ":" not in server_addr:
                retry_addr = f"{server_addr}:25565"
                server, status = await self._lookup_server(retry_addr)
                if status is not None:
                    server_addr = retry_addr

            if status is None:
                return None

            motd_raw = "Unknown"
            if hasattr(status, "description"):
                motd_raw = status.description
            elif hasattr(status, "motd"):
                motd_raw = status.motd.to_minecraft()

            icon = None
            icon = status.icon

            players_list = []
            if status.players.sample is not None:
                players_list = [player.name for player in status.players.sample]

            return {
                "server_addr": server_addr,
                "online": status.players.online,
                "max": status.players.max,
                "latency": round(status.latency, 2),
                "motd_raw": motd_raw,
                "version": status.version.name,
                "protocol": status.version.protocol,
                "players": players_list,
                "server_icon": icon
            }
        except Exception as e:
            logger.error(f"获取服务器状态出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_image_response(self, data_map: dict) -> tuple[bool, str]:
        font_name = self.config["font"]
        drawer = Draw(output_path=self._get_new_image_path(), bg_path=self.bg_name)
        success, result = await drawer.draw_card(data_map, font_name)
        if success:
            return True, result
        else:
            return False, f"❌ 图片生成失败: {result}"

    # 帮助图片生成专用入口
    async def _generate_help_response(self, data_map: dict) -> tuple[bool, str]:
        font_name = self.config["font"]
        drawer = Draw(output_path=self._get_new_image_path(), bg_path=self.bg_name)
        success, result = await drawer.draw_help(data_map, font_name)
        if success:
            return True, result
        else:
            return False, f"❌ 帮助生成失败: {result}"

    # 列表图片生成专用入口
    async def _generate_list_response(self, data_map: dict) -> tuple[bool, str]:
        font_name = self.config["font"]
        drawer = Draw(output_path=self._get_new_image_path(), bg_path=self.bg_name)
        success, result = await drawer.draw_list(data_map, font_name)
        if success:
            return True, result
        else:
            return False, f"❌ 列表生成失败: {result}"

    async def _handle_motd(self, event: AstrMessageEvent, server_addr: str) -> tuple[bool, str]:
        if not server_addr:
            return False, "用法：/mcstatus motd <地址>"

        server_status = await self.get_server_status(server_addr)
        if server_status is None:
             return False, "❌ 无法连接服务器，请检查地址。"

        data_map = {
            "server_icon": server_status.get("server_icon"),
            "motd_raw": server_status.get("motd_raw"),
            "addr": server_status.get("server_addr"),
            "version": server_status.get("version"),
            "protocol": server_status.get("protocol"),
            "latency": server_status.get("latency"),
            "online": server_status.get("online"),
            "max": server_status.get("max"),
            "players": server_status.get("players")
        }

        return await self._generate_image_response(data_map)

    async def _handle_players(self, event: AstrMessageEvent, server_addr: str = "") -> tuple[bool, str]:
        return await self._handle_motd(event, server_addr)

    async def _handle_look(self, event: AstrMessageEvent, server_name: str) -> tuple[bool, str]:
        if not server_name:
            return False, "用法：/mcs look <名称>"
        addr = self.datamanager.get_server_addr(server_name, event.get_group_id(), event.get_sender_id(), self.is_global)
        if addr is None:
            return False, f"❌ 未找到 {server_name}"
        return await self._handle_motd(event, addr)

    async def _handle_list(self, event: AstrMessageEvent) -> tuple[bool, str]:
        data = self.datamanager.get_all_configs(event.get_group_id(), event.get_sender_id(), self.is_global)
        data_map = {
            "servers": data
        }
        return await self._generate_list_response(data_map)

    async def _handle_help(self, event: AstrMessageEvent) -> tuple[bool, str]:
        # 帮助列表：(指令, 描述)
        help_items = [
            ("help", "获取此帮助信息"),
            ("motd <IP>", "获取服务器状态/延迟"),
            ("players <IP>", "获取在线玩家列表(失效)"),
            ("add <Name> <IP>", "添加常用服务器"),
            ("del <Name>", "删除已存服务器"),
            ("look <Name>", "查询已存服务器"),
            ("list", "显示服务器列表"),
            ("clear", "清空所有 (*仅管理)")
        ]

        data_map = {
            "help_items": help_items,
            "version": self.plugin_version,
            "server_icon": None
        }
        return await self._generate_help_response(data_map)

    async def _handle_add(self, event: AstrMessageEvent, server_name: str, server_addr: str) -> tuple[bool, str]:
        if not server_name or not server_addr:
            return False, "用法：/mcs add [名称] [地址]"
        if self.datamanager.add_server_addr(server_name, server_addr, event.get_group_id(), event.get_sender_id(), self.is_global):
            return False, f"✅ 服务器 {server_name} 添加成功！"
        else:
            return False, "❌ 添加失败。"

    async def _handle_del(self, event: AstrMessageEvent, server_name: str) -> tuple[bool, str]:
        if not server_name:
            return False, "用法：/mcs del [名称]"
        if self.datamanager.remove_server_addr(server_name, event.get_group_id(), event.get_sender_id(), self.is_global):
            return False, f"✅ 服务器 {server_name} 删除成功！"
        else:
            return False, "❌ 未找到。"

    async def _handle_set(self, event: AstrMessageEvent, server_name: str, server_addr: str) -> tuple[bool, str]:
        if not server_name or not server_addr:
            return False, "用法：/mcs set [名] [地址]"
        if self.datamanager.update_server_addr(server_name, server_addr, event.get_group_id(), event.get_sender_id(), self.is_global):
            return False, "✅ 更新成功。"
        return False, "❌ 更新失败。"

    async def _handle_clear(self, event: AstrMessageEvent) -> tuple[bool, str]:
        if event.get_sender_id() not in self.admin_list:
            return False, "❌ 权限不足"
        if self.datamanager.clear_all_configs(event.get_group_id(), event.get_sender_id(), self.is_global):
            return False, "✅ 已清空。"
        return False, "❌ 失败。"
