from astrbot.api import logger
from astrbot.api.star import StarTools
from PIL import Image, ImageDraw, ImageFont
import os
import asyncio
from typing import List, Tuple


class Draw:
    def __init__(self,output = f"{StarTools.get_data_dir('mcstatus')}/draw_temp.png"):
        """初始化图片生成器，设置默认输出路径"""
        self.output = output
        os.makedirs(os.path.dirname(self.output), exist_ok=True)

    def draw_text_with_outline(self, draw: ImageDraw.ImageDraw, x: float, y: float,
                               text: str, font: ImageFont.FreeTypeFont,
                               text_color=(255, 255, 255), outline_color=(0, 0, 0),
                               outline_width: int = 1):
        """绘制带描边的单行文字（描边通过多次偏移绘制实现）"""
        # 描边
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        # 正文
        draw.text((x, y), text, font=font, fill=text_color)

    def get_font_paths(self, seted_font: str = "cute_font.ttf") -> List[str]:
        """
        获取优先的字体路径列表（存在的才返回）
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_font_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        custom_font_path = os.path.join(plugin_font_dir, seted_font)

        candidate = [
            custom_font_path,
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/Library/Fonts/Arial Bold.ttf",
            "/Library/Fonts/Microsoft YaHei.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "simhei.ttf",
            "msyh.ttc",
            "msyhbd.ttc",
            "simsun.ttc",
            "arial.ttf",
        ]

        existing = []
        custom_found = False
        for p in candidate:
            try:
                if os.path.exists(p):
                    if p == custom_font_path:
                        custom_found = True
                        existing.insert(0, p)
                    else:
                        existing.append(p)
                else:
                    local = os.path.join(current_dir, p)
                    if os.path.exists(local):
                        if local == custom_font_path:
                            custom_found = True
                            existing.insert(0, local)
                        else:
                            existing.append(local)
            except Exception:
                continue

        if custom_found:
            logger.info(f"[mcstatus]使用自定义字体: {seted_font}")
        else:
            logger.debug(f"[mcstatus]自定义字体未找到: {seted_font}，使用候选字体列表中的可用项")

        return existing

    def find_best_font(self, text: str, max_width: int, font_paths: List[str], base_font_size: int = 60):
        """
        在 font_paths 中查找能适合 max_width 的字体（返回 ImageFont 和最终大小）。
        尝试几种大小，首个通过宽度判断的字体即返回。
        """
        # 依据文本长度粗略调整 base size
        bf = base_font_size
        if len(text) > 30:
            bf = int(bf * 0.6)
        elif len(text) > 20:
            bf = int(bf * 0.8)
        elif len(text) > 10:
            bf = int(bf * 0.9)

        sizes_to_try = [bf, max(8, bf - 6), max(8, bf - 12), bf + 6]

        for font_path in font_paths:
            for size in sizes_to_try:
                try:
                    test_font = ImageFont.truetype(font_path, size)
                    tmp_img = Image.new("RGBA", (10, 10))
                    tmp_draw = ImageDraw.Draw(tmp_img)
                    bbox = tmp_draw.textbbox((0, 0), text, font=test_font)
                    text_w = bbox[2] - bbox[0]
                    if text_w <= max_width * 0.9:  # 留一些边距
                        logger.info(f"[mcstatus]选择字体: {os.path.basename(font_path)} 大小: {size}")
                        return test_font, size
                except Exception:
                    continue

        try:
            if font_paths:
                fallback_path = font_paths[0]
                f = ImageFont.truetype(fallback_path, bf)
                logger.warning("[mcstatus]未找到完全合适字体，使用第一个可用字体")
                return f, bf
        except Exception:
            pass

        logger.warning("[mcstatus]使用系统默认字体（ImageFont.load_default）")
        return ImageFont.load_default(), bf

    def _measure_multiline(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
                           spacing: int = 4) -> Tuple[int, int, List[Tuple[int, int]]]:
        """
        测量多行文本的最大宽度与总高度（返回 max_width, total_height, per_line_sizes）。
        spacing: 行间距像素
        """
        lines = text.splitlines() or [text]
        sizes = []
        max_w = 0
        total_h = 0
        for i, line in enumerate(lines):
            if line == "":
                # 空行要给出高度（用单个空格测量）
                bbox = draw.textbbox((0, 0), " ", font=font)
            else:
                bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            sizes.append((w, h))
            if w > max_w:
                max_w = w
            total_h += h
            if i != len(lines) - 1:
                total_h += spacing
        return max_w, total_h, sizes

    # 渲染方法（左上角60,60）
    async def create_high_quality_image(self, text: str, background: Image.Image, output_path: str,
                                        seted_font: str, font_size: int = 60,
                                        scale_factor: int = 2, spacing: int = 6):
        """
        异步高质量渲染（超采样）
        font_size: 基础字体大小（在 hi-res 上会乘以 scale_factor）
        spacing: 行间距（基于最终字体像素）
        """
        try:
            original_size = background.size
            hi_res_size = (original_size[0] * scale_factor, original_size[1] * scale_factor)

            loop = asyncio.get_event_loop()
            hi_res_bg = await loop.run_in_executor(None, lambda: background.resize(hi_res_size, Image.LANCZOS))
            draw = ImageDraw.Draw(hi_res_bg)
            hi_res_font_size = int(font_size * scale_factor)
            hi_res_spacing = int(spacing * scale_factor)

            font_paths = await loop.run_in_executor(None, lambda: self.get_font_paths(seted_font))
            font, actual_size = await loop.run_in_executor(
                None, lambda: self.find_best_font(text, hi_res_size[0], font_paths, hi_res_font_size)
            )

            max_w, total_h, per_line = self._measure_multiline(draw, text, font, spacing=hi_res_spacing)
            outline_w = max(1, int(scale_factor))

            # 左上角 60,60 起点
            y = 60 * scale_factor
            for idx, line in enumerate(text.splitlines() or [text]):
                w, h = per_line[idx]
                x = 60 * scale_factor  # 左对齐固定 x
                if line == "":
                    y += h + hi_res_spacing
                    continue
                self.draw_text_with_outline(draw, x, y, line, font,
                                            text_color=(255, 255, 255),
                                            outline_color=(0, 0, 0),
                                            outline_width=outline_w)
                y += h + hi_res_spacing

            final_image = await loop.run_in_executor(None, lambda: hi_res_bg.resize(original_size, Image.LANCZOS))
            await loop.run_in_executor(None, lambda: final_image.save(output_path, quality=95, dpi=(300, 300)))
            return True, output_path
        except Exception as e:
            logger.error(f"[mcstatus]高质量渲染出错: {e}")
            return False, str(e)

    async def create_standard_quality_image(self, text: str, background: Image.Image, output_path: str,
                                            seted_font: str, font_size: int = 60, spacing: int = 4):
        """
        异步标准质量渲染（不超采样）
        """
        try:
            loop = asyncio.get_event_loop()
            draw = ImageDraw.Draw(background)
            width, height = background.size

            font_paths = await loop.run_in_executor(None, lambda: self.get_font_paths(seted_font))
            font, actual_size = await loop.run_in_executor(
                None, lambda: self.find_best_font(text, width, font_paths, font_size)
            )

            max_w, total_h, per_line = self._measure_multiline(draw, text, font, spacing=spacing)
            outline_w = max(1, int(1))

            # 左上角 60,60 起点
            y = 60
            for idx, line in enumerate(text.splitlines() or [text]):
                w, h = per_line[idx]
                x = 60  # 左对齐固定 x
                if line == "":
                    y += h + spacing
                    continue
                self.draw_text_with_outline(draw, x, y, line, font,
                                            text_color=(255, 255, 255),
                                            outline_color=(0, 0, 0),
                                            outline_width=outline_w)
                y += h + spacing

            await loop.run_in_executor(None, lambda: background.save(output_path, quality=95, dpi=(300, 300)))
            return True, output_path
        except Exception as e:
            logger.error(f"[mcstatus]标准质量渲染出错: {e}")
            return False, str(e)

    # -------------------- 主入口 & 快速接口 --------------------
    async def create_image_with_text(self,
                                     text: str,
                                     background_path: str = os.path.join(os.path.dirname(__file__), '..', 'assets', 'bg.png'),
                                     output_path: str = None,
                                     seted_font: str = "cute_font.ttf",
                                     font_size: int = 60,
                                     target_size: Tuple[int, int] = None,
                                     min_width: int = 800,
                                     use_high_quality: bool = True,
                                     resize_method: int = Image.LANCZOS,
                                     spacing: int = 4):
        """
        异步生成带文字的图片（自动选择高质量/标准）
        spacing: 行间距（像素）
        """
        try:
            if output_path is None:
                output_path = self.output

            loop = asyncio.get_event_loop()
            # 检查底图是否存在
            if not await loop.run_in_executor(None, os.path.exists, background_path):
                error_msg = f"[mcstatus]错误: 找不到底图文件 {background_path}"
                logger.error(error_msg)
                return False, error_msg

            # 打开并转换模式（保留 alpha）
            background = await loop.run_in_executor(None, lambda: Image.open(background_path).convert("RGBA"))
            logger.info(f"[mcstatus]原始图片尺寸: {background.size}")

            # 最小宽度放大，或调整到目标尺寸
            if background.size[0] < min_width:
                scale = min_width / background.size[0]
                new_height = int(background.size[1] * scale)
                new_size = (min_width, new_height)
                background = await loop.run_in_executor(None, lambda: background.resize(new_size, Image.LANCZOS))
                logger.info(f"[mcstatus]放大图片尺寸为: {new_size}")

            if target_size and len(target_size) == 2:
                background = await loop.run_in_executor(None, lambda: background.resize(target_size, resize_method))
                logger.info(f"[mcstatus]调整图片尺寸为: {target_size}")

            # 选择渲染
            if use_high_quality and len(text) <= 50:
                success, result = await self.create_high_quality_image(
                    text, background, output_path, seted_font, font_size, scale_factor=2, spacing=spacing
                )
            else:
                success, result = await self.create_standard_quality_image(
                    text, background, output_path, seted_font, font_size, spacing=spacing
                )

            if success:
                logger.info(f"[mcstatus]图片生成成功: {output_path}")
                return True, output_path
            else:
                return False, result

        except Exception as e:
            error_msg = f"[mcstatus]生成图片时出错: {e}"
            logger.error(error_msg)
            return False, error_msg

    async def create_motd_image(self,
                                server_name: str,
                                server_addr: str,
                                server_motd: str,
                                player_num: int,
                                player_max_num: int,
                                players: list[str], #在线玩家
                                ping: int
                                ):
        pass