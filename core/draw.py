import asyncio
import base64
import datetime
import io
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from astrbot.api import logger


class Draw:
    def __init__(self, output_path: str, bg_path: str):
        self.output_path = output_path
        self.assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.user_bg_name = bg_path
        self.default_bg_path = os.path.join(self.assets_dir, "bg.jpg")
        self.default_icon_path = os.path.join(self.assets_dir, "default_icon.png")

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        # 基础配置
        self.CARD_WIDTH = 1200
        self.CARD_HEIGHT = 580

        # MC 颜色代码映射
        self.MC_COLORS = {
            "0": (0, 0, 0),       "1": (0, 0, 170),     "2": (0, 170, 0),     "3": (0, 170, 170),
            "4": (170, 0, 0),     "5": (170, 0, 170),   "6": (255, 170, 0),   "7": (170, 170, 170),
            "8": (85, 85, 85),    "9": (85, 85, 255),   "a": (85, 255, 85),   "b": (85, 255, 255),
            "c": (255, 85, 85),   "d": (255, 85, 255),  "e": (255, 255, 85),  "f": (255, 255, 255),
            "g": (221, 214, 5),   "r": (80, 80, 80)
        }

        # 可爱/糖果风格主题
        self.CUTE_THEME = {
            "bg_fallback": (255, 245, 250), "card_bg": (255, 255, 255, 235), "card_border": (255, 220, 230),
            "shadow": (255, 190, 210, 100), "text_main": (90, 80, 105), "text_label": (150, 130, 160),
            "text_footer": (170, 160, 180), "pill_blue": (210, 240, 255), "pill_pink": (255, 225, 235),
            "pill_text_blue": (80, 140, 200), "pill_text_pink": (200, 100, 120),
            "accent": (255, 160, 180), "ping_good": (160, 235, 180),
            "ping_mid": (255, 225, 160), "ping_bad": (255, 180, 180), "progress_bg": (245, 245, 255),
            "progress_fill": (170, 230, 255), "progress_border": (200, 240, 255)
        }

    def get_font(self, font_name: str, size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        paths = [
            os.path.join(self.assets_dir, font_name),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", font_name)
        ]
        for p in paths:
            if os.path.exists(p):
                try: return ImageFont.truetype(p, size)
                except: pass
        try: return ImageFont.truetype("arial rounded mt bold.ttf", size)
        except:
            try: return ImageFont.truetype("arial.ttf", size)
            except: return ImageFont.load_default()

    def decode_icon(self, base64_str: str) -> Image.Image:
        try:
            if not base64_str: raise ValueError
            if "," in base64_str: _, encoded = base64_str.split(",", 1)
            else: encoded = base64_str
            data = base64.b64decode(encoded)
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            return img
        except:
            if os.path.exists(self.default_icon_path): return Image.open(self.default_icon_path).convert("RGBA")
            return Image.new("RGBA", (64, 64), (255, 230, 235))

    def draw_colored_text(self, draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> int:
        default_color = self.CUTE_THEME["text_main"]
        x_start, y_start = xy
        current_x = float(x_start)
        parts = re.split(r"(§[0-9a-fk-or])", text)
        current_color = default_color
        for part in parts:
            if part.startswith("§") and len(part) == 2:
                code = part[1].lower()
                if code in self.MC_COLORS: current_color = self.MC_COLORS[code]
                if code == "r": current_color = default_color
                continue
            if part:
                draw.text((current_x, y_start), part, font=font, fill=current_color)
                if hasattr(draw, "textlength"): length = draw.textlength(part, font=font)
                else:
                    bbox = draw.textbbox((0, 0), part, font=font)
                    length = bbox[2] - bbox[0]
                current_x += length
        return int(current_x)

    def draw_cute_label(self, draw, x, y, text, font, bg_color, text_color=None):
        if text_color is None: text_color = self.CUTE_THEME["text_label"]
        bbox = draw.textbbox((x, y), text, font=font)
        padding_x, padding_y = 12, 4
        bg_box = (bbox[0] - padding_x, bbox[1] - padding_y, bbox[2] + padding_x, bbox[3] + padding_y)
        draw.rounded_rectangle(bg_box, radius=15, fill=bg_color)
        draw.text((x, y), text, font=font, fill=text_color)
        return bg_box[2]

    async def _init_canvas_no_icon(self, W, H) -> tuple[Image.Image, ImageDraw.ImageDraw, int, int]:
        loop = asyncio.get_event_loop()

        # 背景
        bg_path = self.default_bg_path
        user_bg = os.path.join(self.assets_dir, self.user_bg_name)
        if os.path.exists(user_bg): bg_path = user_bg

        if os.path.exists(bg_path):
            bg = await loop.run_in_executor(None, Image.open, bg_path)
            bg = ImageOps.fit(bg, (W, H), method=Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(12))
            bg = bg.convert("RGBA")
            white_overlay = Image.new("RGBA", (W, H), (255, 255, 255, 100))
            bg = Image.alpha_composite(bg, white_overlay)
        else:
            bg = Image.new("RGBA", (W, H), self.CUTE_THEME["bg_fallback"])

        # 卡片容器
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)

        margin = 35
        card_box = (margin, margin, W-margin, H-margin)
        card_radius = 35
        shadow_offset = 8
        draw_overlay.rounded_rectangle(
            (card_box[0]+shadow_offset, card_box[1]+shadow_offset, card_box[2]+shadow_offset, card_box[3]+shadow_offset),
            radius=card_radius, fill=self.CUTE_THEME["shadow"]
        )
        draw_overlay.rounded_rectangle(card_box, radius=card_radius, fill=self.CUTE_THEME["card_bg"])
        draw_overlay.rounded_rectangle(card_box, radius=card_radius, outline=self.CUTE_THEME["card_border"], width=3)

        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        content_x = margin + 40
        content_y = margin + 40
        return bg, draw, content_x, content_y

    # 通用画布初始化
    async def _init_canvas(self, W, H, icon_data) -> tuple[Image.Image, ImageDraw.ImageDraw, int, int]:
        loop = asyncio.get_event_loop()

        # 背景
        bg_path = self.default_bg_path
        user_bg = os.path.join(self.assets_dir, self.user_bg_name)
        if os.path.exists(user_bg): bg_path = user_bg

        if os.path.exists(bg_path):
            bg = await loop.run_in_executor(None, Image.open, bg_path)
            bg = ImageOps.fit(bg, (W, H), method=Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(12))
            bg = bg.convert("RGBA")
            white_overlay = Image.new("RGBA", (W, H), (255, 255, 255, 100))
            bg = Image.alpha_composite(bg, white_overlay)
        else:
            bg = Image.new("RGBA", (W, H), self.CUTE_THEME["bg_fallback"])

        # 卡片容器
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)

        margin = 35
        card_box = (margin, margin, W-margin, H-margin)
        card_radius = 35
        shadow_offset = 8
        draw_overlay.rounded_rectangle(
            (card_box[0]+shadow_offset, card_box[1]+shadow_offset, card_box[2]+shadow_offset, card_box[3]+shadow_offset),
            radius=card_radius, fill=self.CUTE_THEME["shadow"]
        )
        draw_overlay.rounded_rectangle(card_box, radius=card_radius, fill=self.CUTE_THEME["card_bg"])
        draw_overlay.rounded_rectangle(card_box, radius=card_radius, outline=self.CUTE_THEME["card_border"], width=3)

        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # 图标
        icon_size = 150
        icon_x, icon_y = margin + 40, margin + 45
        icon_img = self.decode_icon(icon_data)
        icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (icon_size, icon_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, icon_size, icon_size), fill=255)
        ring_offset = 6
        draw.ellipse(
            (icon_x - ring_offset, icon_y - ring_offset, icon_x + icon_size + ring_offset, icon_y + icon_size + ring_offset),
            fill=self.CUTE_THEME["bg_fallback"], outline=self.CUTE_THEME["card_border"], width=3
        )
        bg.paste(icon_img, (icon_x, icon_y), mask)

        content_x = icon_x + icon_size + 50
        content_y = icon_y + 5
        return bg, draw, content_x, content_y

    async def draw_list(self, data_map: dict, seted_font_name: str) -> tuple[bool, str]:
        try:
            loop = asyncio.get_event_loop()
            W = self.CARD_WIDTH

            font_title = self.get_font(seted_font_name, 42)
            font_item = self.get_font(seted_font_name, 32)
            font_addr = self.get_font(seted_font_name, 26)
            font_footer = self.get_font(seted_font_name, 18)

            servers = data_map.get("servers", {})

            # 计算需要的高度
            temp_img = Image.new("RGBA", (W, 100))
            temp_draw = ImageDraw.Draw(temp_img)

            margin = 35
            content_x = margin + 40
            max_text_w = W - margin * 2 - 80

            y_offset = margin + 40
            y_offset += 80 # 标题下方间距

            server_lines = []

            if not servers:
                y_offset += 60
            else:
                for idx, (name, addr) in enumerate(servers.items(), 1):
                    name_text = f"{idx}. {name}"
                    addr_text = f"地址: {addr}"

                    # 换行处理
                    def wrap_text(text, font, max_w):
                        lines = []
                        current_line = ""
                        for char in text:
                            test_line = current_line + char
                            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                            if bbox[2] - bbox[0] > max_w and current_line:
                                lines.append(current_line)
                                current_line = char
                            else:
                                current_line = test_line
                        if current_line:
                            lines.append(current_line)
                        return lines

                    name_wrapped = wrap_text(name_text, font_item, max_text_w)
                    addr_wrapped = wrap_text(addr_text, font_addr, max_text_w - 40)

                    server_lines.append({
                        "name_lines": name_wrapped,
                        "addr_lines": addr_wrapped,
                        "is_blue": (idx % 2 == 1)
                    })

                    y_offset += len(name_wrapped) * 45 + len(addr_wrapped) * 35 + 25 # 每个服务器的间距

            H = int(y_offset + 80) # 底部留白和footer
            H = max(H, 300) # 最小高度

            bg, draw, content_x, content_y = await self._init_canvas_no_icon(W, H)

            # 绘制标题
            draw.text((content_x, content_y), "服务器列表", font=font_title, fill=self.CUTE_THEME["text_main"])

            # 绘制小胶囊: 共 x 个
            count_x = content_x + 240
            self.draw_cute_label(draw, count_x, content_y + 10, f"共 {len(servers)} 个", font_addr, self.CUTE_THEME["pill_pink"], self.CUTE_THEME["pill_text_pink"])

            current_y = content_y + 80

            if not servers:
                draw.text((content_x, current_y), "暂无已保存的服务器", font=font_item, fill=self.CUTE_THEME["text_main"])
            else:
                for srv in server_lines:
                    is_blue = srv["is_blue"]
                    pill_text = self.CUTE_THEME["pill_text_blue"] if is_blue else self.CUTE_THEME["pill_text_pink"]

                    # 绘制名称
                    for line in srv["name_lines"]:
                        draw.text((content_x, current_y), line, font=font_item, fill=pill_text)
                        current_y += 45

                    # 绘制地址
                    for line in srv["addr_lines"]:
                        draw.text((content_x + 40, current_y), line, font=font_addr, fill=self.CUTE_THEME["text_label"])
                        current_y += 35

                    current_y += 15 # 额外间距

            # 底部右下角信息
            current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            footer_text_1 = f"查询时间：{current_time}"
            footer_text_2 = "astrbot_plugin_mcstatus | Design by 清蒸云鸭"

            def draw_right_align(text, y, font, color):
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                x = W - margin - w - 10
                draw.text((x, y), text, font=font, fill=color)

            footer_base_y = H - margin - 60
            draw_right_align(footer_text_1, footer_base_y, font_footer, self.CUTE_THEME["text_footer"])
            draw_right_align(footer_text_2, footer_base_y + 25, font_footer, self.CUTE_THEME["text_footer"])

            await loop.run_in_executor(None, bg.save, self.output_path)
            return True, self.output_path

        except Exception as e:
            logger.error(f"服务器列表绘图失败: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)

    # [大幅美化] 帮助菜单绘制逻辑
    async def draw_help(self, data_map: dict, seted_font_name: str) -> tuple[bool, str]:
        try:
            loop = asyncio.get_event_loop()
            W = self.CARD_WIDTH
            # [修改] 高度改为 800，紧凑且美观
            H = 800

            bg, draw, content_x, content_y = await self._init_canvas(W, H, data_map.get("server_icon", ""))

            font_title = self.get_font(seted_font_name, 42)
            font_subtitle = self.get_font(seted_font_name, 26)
            font_cmd = self.get_font(seted_font_name, 28) # 指令字体
            font_desc = self.get_font(seted_font_name, 26) # 描述字体
            font_footer = self.get_font(seted_font_name, 18)

            # --- 标题区域 ---
            plugin_ver = data_map.get("version", "1.0.0")
            draw.text((content_x, content_y + 10), "MCStatus 插件帮助", font=font_title, fill=self.CUTE_THEME["text_main"])
            # 绘制版本号小胶囊
            ver_x = content_x + 360
            self.draw_cute_label(draw, ver_x+15, content_y + 20, f"Ver {plugin_ver}", font_subtitle, self.CUTE_THEME["pill_pink"], self.CUTE_THEME["pill_text_pink"])

            # --- 列表区域 ---
            help_items = data_map.get("help_items", [])
            start_y = content_y + 90
            line_height = 65 # 行高

            for i, item in enumerate(help_items):
                cmd_str, desc_str = item

                # 交替颜色 (蓝/粉)
                is_blue = (i % 2 == 0)
                pill_bg = self.CUTE_THEME["pill_blue"] if is_blue else self.CUTE_THEME["pill_pink"]
                pill_text = self.CUTE_THEME["pill_text_blue"] if is_blue else self.CUTE_THEME["pill_text_pink"]

                # 绘制指令胶囊 (左侧)
                # 计算指令文本宽度以调整胶囊大小，但给一个最小宽度保持整齐
                cmd_bbox = draw.textbbox((0, 0), cmd_str, font=font_cmd)
                cmd_w = cmd_bbox[2] - cmd_bbox[0]
                pill_w = max(cmd_w + 40, 180) # 最小宽度180

                pill_box = (content_x, start_y, content_x + pill_w, start_y + 45)
                draw.rounded_rectangle(pill_box, radius=22, fill=pill_bg)

                # 居中绘制指令文字
                text_x = content_x + (pill_w - cmd_w) / 2
                draw.text((text_x, start_y + 6), cmd_str, font=font_cmd, fill=pill_text)

                # 绘制描述文字 (右侧)
                draw.text((content_x + pill_w + 20, start_y + 8), f"→ {desc_str}", font=font_desc, fill=self.CUTE_THEME["text_main"])

                start_y += line_height

            # --- 底部提示 ---
            tip_y = start_y + 10
            draw.text((content_x, tip_y), "Tip: 地址支持域名或IP:端口 (如 example.com:25566)", font=font_subtitle, fill=self.CUTE_THEME["text_label"])

            # --- 底部右下角信息 (严格对齐修复) ---
            margin = 35
            current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            footer_text_1 = f"查询时间：{current_time}"
            footer_text_2 = "astrbot_plugin_mcstatus | Design by 清蒸云鸭"

            # 严格计算右对齐坐标
            def draw_right_align(text, y, font, color):
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                # x = 画布宽度 - 边距 - 文字宽度 - 额外的一点padding(确保不贴边)
                x = W - margin - w - 10
                draw.text((x, y), text, font=font, fill=color)

            # 定位到底部
            footer_base_y = H - margin - 60
            draw_right_align(footer_text_1, footer_base_y, font_footer, self.CUTE_THEME["text_footer"])
            draw_right_align(footer_text_2, footer_base_y + 25, font_footer, self.CUTE_THEME["text_footer"])

            await loop.run_in_executor(None, bg.save, self.output_path)
            return True, self.output_path
        except Exception as e:
            logger.error(f"帮助图片生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)

    # 服务器状态卡片 (保持之前逻辑不变，仅复用 _init_canvas)
    async def draw_card(self, data_map: dict, seted_font_name: str) -> tuple[bool, str]:
        try:
            loop = asyncio.get_event_loop()
            W, H = self.CARD_WIDTH, self.CARD_HEIGHT

            bg, draw, content_x, content_y = await self._init_canvas(W, H, data_map.get("server_icon", ""))

            font_title = self.get_font(seted_font_name, 42)
            font_motd2 = self.get_font(seted_font_name, 28)
            font_label = self.get_font(seted_font_name, 24)
            font_val = self.get_font(seted_font_name, 28)
            font_small = self.get_font(seted_font_name, 22)
            font_footer = self.get_font(seted_font_name, 18)

            motd_raw = data_map.get("motd_raw", "Unknown Server")
            motd_lines = motd_raw.split("\n")
            self.draw_colored_text(draw, (content_x, content_y), motd_lines[0], font_title)
            if len(motd_lines) > 1:
                self.draw_colored_text(draw, (content_x, content_y + 55), motd_lines[1], font_motd2)

            grid_y = content_y + 120
            col_gap = 240

            def draw_field(x, y, label_text, value_text, label_pill_color=None, value_color=None, max_len=0):
                bg_col = label_pill_color if label_pill_color else self.CUTE_THEME["pill_pink"]
                self.draw_cute_label(draw, x, y, label_text, font_label, bg_col)
                val_str = str(value_text)
                fill_col = value_color if value_color else self.CUTE_THEME["text_main"]
                start_y = y + 38
                if max_len > 0 and len(val_str) > max_len:
                    bbox = font_val.getbbox("Ay")
                    line_height = (bbox[3] - bbox[0]) + 5
                    for i in range(0, len(val_str), max_len):
                        chunk = val_str[i:i + max_len]
                        draw.text((x + 5, start_y), chunk, font=font_val, fill=fill_col)
                        start_y += line_height
                else:
                    draw.text((x + 5, start_y), val_str, font=font_val, fill=fill_col)

            draw_field(content_x, grid_y, "地址", data_map.get("addr", "Unknown"), max_len=10)
            draw_field(content_x + col_gap, grid_y, "版本", data_map.get("version", "Unknown"),
                       label_pill_color=self.CUTE_THEME["pill_blue"],
                       value_color=self.CUTE_THEME["pill_text_blue"])
            draw_field(content_x + col_gap*2, grid_y, "协议", data_map.get("protocol", "?"))
            latency = data_map.get("latency", 0)
            lat_color = self.CUTE_THEME["ping_good"] if latency < 100 else (self.CUTE_THEME["ping_mid"] if latency < 200 else self.CUTE_THEME["ping_bad"])
            draw_field(content_x + col_gap*3, grid_y, "延迟", f"{latency}ms", value_color=lat_color)

            list_y = grid_y + 130
            players = data_map.get("players", [])
            self.draw_cute_label(draw, content_x, list_y, "在线列表", font_label, self.CUTE_THEME["pill_blue"], self.CUTE_THEME["pill_text_blue"])
            display_limit = 4
            if not players: player_str = "当前没有可爱的玩家在线哦~"
            else:
                player_str = ", ".join(players[:display_limit])
                if len(players) > display_limit: player_str += f" 等 {len(players)} 人"
            draw.text((content_x + 5, list_y + 40), player_str, font=font_small, fill=self.CUTE_THEME["text_main"])

            margin = 35
            bar_h = 20
            bar_y = H - margin - 90
            bar_x = margin + 40
            bar_w = W - (margin * 2) - 80

            online = data_map.get("online", 0)
            max_p = data_map.get("max", 1)
            if max_p == 0: max_p = 1
            ratio = min(online / max_p, 1.0)

            draw.text((bar_x + 5, bar_y - 38), f"在线人数: {online} / {max_p}", font=font_val, fill=self.CUTE_THEME["text_main"])
            bar_radius = bar_h / 2
            draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                                   radius=bar_radius, fill=self.CUTE_THEME["progress_bg"], outline=self.CUTE_THEME["progress_border"], width=2)
            if ratio > 0:
                fill_w = int(bar_w * ratio)
                fill_w = max(fill_w, bar_h)
                draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h),
                                       radius=bar_radius, fill=self.CUTE_THEME["progress_fill"])

            # 底部信息
            def draw_right_align(text, y, font, color):
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                x = W - margin - w - 10
                draw.text((x, y), text, font=font, fill=color)

            current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
            footer_text_1 = f"查询时间：{current_time}"
            footer_text_2 = "astrbot_plugin_mcstatus | Design by 清蒸云鸭"
            footer_base_y = bar_y + 35
            draw_right_align(footer_text_1, footer_base_y, font_footer, self.CUTE_THEME["text_footer"])
            draw_right_align(footer_text_2, footer_base_y + 22, font_footer, self.CUTE_THEME["text_footer"])

            await loop.run_in_executor(None, bg.save, self.output_path)
            return True, self.output_path

        except Exception as e:
            logger.error(f"绘图失败: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
