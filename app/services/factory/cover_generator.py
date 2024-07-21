# -- coding: utf-8 --
# @Time : 2024/7/21 08:29
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : cover_generator.py
# @Software: PyCharm
import random

from PIL import ImageFont
from loguru import logger
from moviepy.editor import *

from app.constant.video_const import PUNCTUATIONS
from app.settings import movies_config

model_size = movies_config.whisper.get("model_size", "large-v3")
device = movies_config.whisper.get("device", "cpu")
compute_type = movies_config.whisper.get("compute_type", "int8")
model = None


def create_title_clip(params, title, video_width, video_height, font_path, cover_mode="text", video_path=None,
                      random_bg=True):
    """生成视频封面"""
    width_factor = 0.4  # 字幕显示的区域占比视频画面宽度的比例
    font_size_factor = 1.6  # 封面标题字体大小与字幕字体大小倍率
    duration = 0.5  # 视频封面播放的时长秒
    logger.info(f"生成视频封面,宽度占比：{width_factor},字体放大倍率：{font_size_factor},播放时长:{duration}, 封面模式: {cover_mode}")

    if params.weibo_title:
        # 如果有微博热搜，就用热搜文本作为封面文字
        title = params.weibo_title

    def wrap_title_text(text, max_width, font_path, fontsize):
        font = ImageFont.truetype(font_path, fontsize)

        def get_text_size(inner_text):
            inner_text = inner_text.strip()
            left, top, right, bottom = font.getbbox(inner_text)
            return right - left, bottom - top

        lines = []
        current_line = ""
        for char in text:
            # 如果标题中有中文标点符号就换行
            if char in PUNCTUATIONS:
                lines.append(current_line.strip())
                current_line = ""
            else:
                current_line += char
                width, _ = get_text_size(current_line)
                if width > max_width:
                    lines.append(current_line.strip())
                    current_line = ""
        if current_line:
            lines.append(current_line.strip())

        wrapped_text = "\n".join(lines)
        return wrapped_text

    wrapped_title = wrap_title_text(title, video_width * width_factor, font_path, params.font_size * font_size_factor)

    if cover_mode == "text":
        # 确定背景颜色
        if random_bg:
            bg_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            logger.info(f"封面背景颜色随机： {bg_color}")
        else:
            bg_color = params.text_background_color
            logger.info(f"封面背景颜色 {bg_color}")

        # 创建纯色背景的文字剪辑
        text_clip = TextClip(
            wrapped_title,
            font=font_path,
            fontsize=params.font_size * font_size_factor,
            color=params.text_fore_color,
            bg_color=bg_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
            size=(video_width, video_height),
            method='label'
        ).set_duration(duration).set_position(("center", "center"))

        return text_clip

    elif cover_mode == "video_frame" and video_path:
        # 从视频中随机截取一帧作为背景
        video = VideoFileClip(video_path)
        frame_time = random.uniform(0, video.duration)
        frame = video.get_frame(frame_time)

        # 创建视频帧背景的图片剪辑
        background_clip = ImageClip(frame).set_duration(duration).set_position(("center", "center")).resize(
            (video_width, video_height))

        # 创建文字剪辑
        text_clip = TextClip(
            wrapped_title,
            font=font_path,
            fontsize=params.font_size * font_size_factor,
            color=params.text_fore_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
            method='caption'
        ).set_duration(duration).set_position(("center", "center"))

        # 将文字剪辑叠加到背景剪辑上
        final_clip = CompositeVideoClip([background_clip, text_clip])

        return final_clip

    else:
        raise ValueError("Invalid cover_mode or missing video_path for video_frame mode")
