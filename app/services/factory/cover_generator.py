# -- coding: utf-8 --
# @Time : 2024/7/21 08:29
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : cover_generator.py
# @Software: PyCharm
import random

import jieba
from PIL import ImageFont
from loguru import logger
from moviepy.editor import *

from app.constant.video_const import PUNCTUATIONS
def create_title_clip(params, title, video_width, video_height, images_path, font_path, video_path=None, cover_mode="text", random_bg=True):
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
            bbox = font.getbbox(inner_text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]

        words = list(jieba.cut(text))
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word
            width, _ = get_text_size(test_line)
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        wrapped_text = "\n".join(lines)
        return wrapped_text

    max_text_width = video_width * width_factor
    wrapped_title = wrap_title_text(title, max_text_width, font_path, params.font_size * font_size_factor)

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
            method='caption',
            size=(max_text_width, None)  # 设置文本框的宽度，自动调整高度
        ).set_duration(duration).set_position(("center", "center"))

        return text_clip

    elif cover_mode == "video_frame" and video_path:
        # 从视频中随机截取一帧作为背景
        video = VideoFileClip(video_path)
        frame_time = random.uniform(0, video.duration)
        frame = video.get_frame(frame_time)

        # 创建视频帧背景的图片剪辑
        background_clip = ImageClip(frame).set_duration(duration).resize(height=video_height).set_position(("center", "center"))

        # 如果有微博图片路径，随机选择一张包含"big"的作为背景
        combined_background = background_clip
        if images_path:
            big_images = [img for img in images_path if "big" in img]
            if big_images:
                weibo_image_path = random.choice(big_images)
                weibo_image = ImageClip(weibo_image_path).set_duration(duration).resize(height=video_height).set_position(("center", "center"))
                combined_background = CompositeVideoClip([background_clip, weibo_image])

        # 确定背景颜色
        text_bg_color = params.text_background_color if not random_bg else "#{:06x}".format(random.randint(0, 0xFFFFFF))

        # 创建文字剪辑，并设置背景颜色
        text_clip = TextClip(
            wrapped_title,
            font=font_path,
            fontsize=params.font_size * font_size_factor,
            color=params.text_fore_color,
            bg_color=text_bg_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
            method='caption',
            size=(max_text_width, None)  # 设置文本框的宽度，自动调整高度
        ).set_duration(duration).set_position(("center", "center"))

        # 将文字剪辑叠加到组合背景上
        final_clip = CompositeVideoClip([combined_background, text_clip])

        return final_clip

    else:
        raise ValueError("Invalid cover_mode or missing video_path for video_frame mode")