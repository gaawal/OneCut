import asyncio
import multiprocessing
import platform
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
from PIL import Image, ImageFont
from PIL import ImageFilter
from loguru import logger
from moviepy.editor import *
from moviepy.editor import ImageClip
from moviepy.video.fx.resize import resize
from moviepy.video.tools.subtitles import SubtitlesClip

from app.schemas.movies import VideoAspect, VideoConcatMode
from app.services.factory.cover_generator import create_title_clip
from app.utils import utils
from app.utils.utils import get_font_path

# 获取CPU核心数
cpu_count = multiprocessing.cpu_count()

# 设置线程池大小为CPU核心数的2倍
thread_pool_size = cpu_count * 2
executor = ThreadPoolExecutor(max_workers=thread_pool_size)  # 使用线程池执行异步任务
logger.info(f"设置线程池大小为CPU核心数的2倍:{thread_pool_size}")

# 创建一个信号量对象来限制同时打开的文件数
semaphore = asyncio.Semaphore(50)


def get_ffmpeg_params():
    system = platform.system().lower()
    if system == "darwin":  # macOS
        return [
            '-c:v', 'h264_videotoolbox',  # 使用macOS的硬件加速
            '-preset', 'fast',  # 编码速度快，质量和压缩效率较平衡
            '-b:v', '4000k',  # 目标比特率4000kbps，较高质量
            '-profile:v', 'high',  # 使用高质量配置文件
            '-movflags', 'faststart'  # 优化文件以便快速启动播放
        ]
    elif system == "windows":
        return [
            '-c:v', 'h264_nvenc',  # 使用NVIDIA硬件加速
            '-preset', 'fast',
            '-b:v', '4000k',
            '-profile:v', 'high',
            '-movflags', 'faststart'
        ]
    elif system == "linux":
        return [
            '-c:v', 'h264_nvenc',  # 使用NVIDIA硬件加速
            '-preset', 'fast',
            '-b:v', '4000k',
            '-profile:v', 'high',
            '-movflags', 'faststart'
        ]
    else:
        return [
            '-c:v', 'libx264',  # 使用软件编码
            '-preset', 'fast',
            '-crf', '20',  # 固定速率因子20，较高质量
            '-movflags', 'faststart'
        ]


async def create_video_clip_async(video_path):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, VideoFileClip, video_path)


async def create_audio_clip_async(audio_path):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, AudioFileClip, audio_path)


async def subclip_async(clip, start_time, end_time):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, clip.subclip, start_time, end_time)


async def resize_clip_async(clip, video_width, video_height):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, resize_clip, clip, video_width, video_height)


async def write_videofile_async(video_clip, filename, **kwargs):
    ffmpeg_params = get_ffmpeg_params()
    async with semaphore:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, lambda: video_clip.write_videofile(
            filename,
            codec='libx264',
            ffmpeg_params=ffmpeg_params,
            **kwargs
        ))


def resize_clip(clip, video_width, video_height):
    clip_w, clip_h = clip.size
    if clip_w != video_width or clip_h != video_height:
        clip_ratio = clip_w / clip_h
        video_ratio = video_width / video_height

        if clip_ratio == video_ratio:
            clip = resize(clip, (video_width, video_height))
        else:
            if clip_ratio > video_ratio:
                scale_factor = video_width / clip_w
            else:
                scale_factor = video_height / clip_h

            new_width = int(clip_w * scale_factor)
            new_height = int(clip_h * scale_factor)
            clip_resized = resize(clip, newsize=(new_width, new_height))

            background = ColorClip(size=(video_width, video_height), color=(0, 0, 0))
            clip = CompositeVideoClip([background.set_duration(clip.duration), clip_resized.set_position("center")])
        logger.info(f"调整视频分辨率为:{video_width} x {video_height}, 原始素材分辨率为:{clip_w} x {clip_h}")
    return clip


async def combine_videos(
        combined_video_path,
        video_paths,
        split_video_paths,
        audio_file,
        video_aspect=VideoAspect.portrait,
        video_concat_mode=VideoConcatMode.random,
        max_clip_duration=5,
        images_files=[],
):
    start_time = datetime.now()
    start_timestamp = time.time()
    logger.info(f"开始合并视频任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    audio_clip = await create_audio_clip_async(audio_file)
    audio_duration = audio_clip.duration
    logger.info(f"预计视频总时长 {audio_duration}（秒）")
    if audio_duration < 60:
        audio_duration = 60.2
        logger.info(f"调整视频总时长为 {audio_duration}（秒）")
    req_dur = max_clip_duration
    logger.info(f"单个视频素材片段最大时长 {req_dur}（秒）")
    output_dir = os.path.dirname(combined_video_path)
    aspect = VideoAspect(video_aspect)
    video_width, video_height = aspect.to_resolution()

    clips = []
    video_duration = 0

    # Step 1: 添加 split_video_paths 中第一个片段的前 5 秒
    if split_video_paths:
        MIN_DURATION = 15
        split_video_file = split_video_paths[0]
        first_split_clip = await create_video_clip_async(split_video_file)
        first_split_clip = await subclip_async(first_split_clip, 0, min(MIN_DURATION, first_split_clip.duration))

        # 处理分辨率不同的情况，使用画中画效果
        split_clip_w, split_clip_h = first_split_clip.size
        if split_clip_w != video_width or split_clip_h != video_height:
            # 背景模糊处理
            logger.info("# 处理分辨率不同的情况，使用画中画效果")
            background_clip = first_split_clip.resize(newsize=(video_width, video_height))
            background_clip = apply_blur(background_clip, blur_radius=70)
            # 缩放原始片段高度一致
            first_split_clip = first_split_clip.resize(height=video_height)
            first_split_clip = first_split_clip.set_position(("center", "center"))
            first_split_clip = CompositeVideoClip([background_clip, first_split_clip])

        clips.append(first_split_clip)
        video_duration += first_split_clip.duration
        logger.info(f"添加微博视频片段前 {MIN_DURATION} 秒，当前片段时长 {video_duration:.2f} 秒")

    # Step 2: 处理其他 video_paths 的视频片段
    raw_clips = []
    raw_clips_start_time = time.time()
    for video_path in video_paths:
        cache_dir = utils.cache_videos_dir()
        video_file = os.path.join(cache_dir, f"{video_path}")
        clip = await create_video_clip_async(video_file)
        clip = clip.without_audio()
        clip_duration = clip.duration
        start_time = 0

        while start_time < clip_duration:
            end_time = min(start_time + max_clip_duration, clip_duration)
            split_clip = await subclip_async(clip, start_time, end_time)

            # 调整分辨率以适应目标视频
            split_clip = resize_clip(split_clip, video_width, video_height)

            raw_clips.append(split_clip)
            start_time = end_time
            if video_concat_mode == VideoConcatMode.sequential:
                break
    logger.info(f"原始片段准备耗时: {time.time() - raw_clips_start_time:.2f} 秒")

    # Step 3: 随机混合 raw_clips，并插入 split_video_paths 的片段
    if video_concat_mode == VideoConcatMode.random:
        random.shuffle(raw_clips)

    if split_video_paths:
        split_clips = []
        for split_video_path in split_video_paths[1:]:  # 跳过第一个片段，因为它已经被添加
            split_clip = await create_video_clip_async(split_video_path)
            split_clip = resize_clip(split_clip, video_width, video_height)
            # 如果分辨率不同，也应用模糊背景处理
            if split_clip.size != (video_width, video_height):
                background_clip = split_clip.resize(newsize=(video_width, video_height))
                background_clip = apply_blur(background_clip, blur_radius=70)
                split_clip = split_clip.resize(height=video_height)
                split_clip = split_clip.set_position(("center", "center"))
                split_clip = CompositeVideoClip([background_clip, split_clip])

            split_clips.append(split_clip)

        combined_clips = []
        for clip in raw_clips:
            if split_clips and random.random() > 0.6:  # 60% 概率插入 split_clip
                combined_clips.append(split_clips.pop(0))
            combined_clips.append(clip)
        raw_clips = combined_clips

    # Step 4: 叠加图片素材（如果当前片段不是 split_video_paths 的视频）
    if images_files:
        image_clips = await add_image_clips(images_files, video_width, video_height, clip_duration=max_clip_duration)
        composite_clips = []
        for i, clip in enumerate(raw_clips):
            if isinstance(clip, ImageClip):
                continue  # 不在 split_video_paths 片段上叠加图片
            img_clip = image_clips[i % len(image_clips)]
            composite_clip = CompositeVideoClip([clip, img_clip])
            composite_clips.append(composite_clip)
        raw_clips = composite_clips

    # Step 5: 合并片段直到总时长达到音频时长
    while video_duration < audio_duration:
        for clip in raw_clips:
            if (audio_duration - video_duration) < clip.duration:
                clip = await subclip_async(clip, 0, (audio_duration - video_duration))
            elif req_dur < clip.duration:
                clip = await subclip_async(clip, 0, req_dur)
            clip = clip.set_fps(30)

            clips.append(clip)
            video_duration += clip.duration

    combined_start_time = time.time()
    video_clip = concatenate_videoclips(clips)
    video_clip = video_clip.set_fps(30)
    logger.info(f"合并视频片段耗时: {time.time() - combined_start_time:.2f} 秒")

    write_start_time = time.time()
    await write_videofile_async(video_clip, filename=combined_video_path,
                                logger=None, temp_audiofile_path=output_dir, audio_codec="aac", fps=30)

    # 确保所有打开的资源都关闭
    for clip in raw_clips:
        clip.close()
    for clip in clips:
        clip.close()
    video_clip.close()
    audio_clip.close()

    logger.success(f"写入视频文件耗时: {time.time() - write_start_time:.2f} 秒")
    logger.success(f"合并视频总耗时: {time.time() - start_timestamp:.2f} 秒")

    return combined_video_path


def apply_blur(clip, blur_radius=70):
    def blur_frame(get_frame, t):
        frame = get_frame(t)
        pil_image = Image.fromarray(frame)
        blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        return np.array(blurred_image)

    return clip.fl(blur_frame)


async def generate_video(task_id, title, combined_video_path, images_path, audio_path, bgm_path, subtitle_path,
                         output_file, params, draft, split_video_paths=None):
    start_time = datetime.now()
    start_timestamp = time.time()
    logger.info(f"开始生成视频任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    aspect = VideoAspect(params.video_aspect)
    video_width, video_height = aspect.to_resolution()

    logger.info(f"开始生成视频，视频尺寸: {video_width} x {video_height}")
    logger.info(f"  ① 合成视频文件: {combined_video_path}")
    logger.info(f"  ② 人声文件: {audio_path}")
    logger.info(f"  ③ 背景音乐: {bgm_path}")
    logger.info(f"  ④ 字幕文件: {subtitle_path}")
    logger.info(f"  ⑤ 目标输出视频: {output_file}")
    output_dir = os.path.dirname(output_file)

    font_path = get_font_path(params)

    # 生成 title_clip
    cover_mode = "video_frame"
    random_bg = True
    title_clip = create_title_clip(params, title, video_width, video_height, images_path, font_path,
                                   video_path=combined_video_path,
                                   cover_mode=cover_mode, random_bg=random_bg)

    def create_text_clip(text, duration, start_time):
        max_width = video_width * 0.9
        wrapped_txt, txt_height = wrap_text(text, max_width=max_width, font=font_path, fontsize=params.font_size)

        _clip = TextClip(
            wrapped_txt,
            font=font_path,
            fontsize=params.font_size,
            color=params.text_fore_color,
            bg_color=params.text_background_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
            print_cmd=False,
        )
        _clip = _clip.set_start(start_time)
        _clip = _clip.set_duration(duration)
        if params.subtitle_position == "bottom":
            _clip = _clip.set_position(("center", video_height * 0.95 - _clip.h))
        elif params.subtitle_position == "top":
            _clip = _clip.set_position(("center", video_height * 0.1))
        else:
            _clip = _clip.set_position(("center", "center"))

        return _clip

    # 加载 combine_videos 生成的视频
    combined_video_clip = await create_video_clip_async(combined_video_path)

    audio_clip = await create_audio_clip_async(audio_path)
    audio_clip = audio_clip.volumex(params.voice_volume)

    # 先合成音频、字幕和视频
    if subtitle_path and os.path.exists(subtitle_path):
        sub = SubtitlesClip(subtitles=subtitle_path, encoding="utf-8")
        text_clips = [create_text_clip(item[1], item[0][1] - item[0][0], item[0][0]) for item in sub.subtitles]
        combined_video_clip = CompositeVideoClip([combined_video_clip, *text_clips])

    if bgm_path:
        try:
            bgm_clip = await create_audio_clip_async(bgm_path)
            bgm_clip = bgm_clip.volumex(params.bgm_volume).audio_fadeout(3)
            bgm_clip = afx.audio_loop(bgm_clip, duration=combined_video_clip.duration)
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"添加背景音乐失败: {str(e)}")

    combined_video_clip = combined_video_clip.set_audio(audio_clip)

    # 再在前面拼接 split_video_paths 中的第一个视频片段
    if split_video_paths:
        split_video_file = split_video_paths[0]
        split_clip = await create_video_clip_async(split_video_file)
        if split_clip.duration > 15:
            split_clip = await subclip_async(split_clip, 0, 15)  # 只截取前 15 秒

        # 处理分辨率不同的情况，使用画中画效果
        split_clip_w, split_clip_h = split_clip.size
        if split_clip_w != video_width or split_clip_h != video_height:
            # 背景模糊处理
            logger.info("# 处理分辨率不同的情况，使用画中画效果")
            background_clip = split_clip.resize(newsize=(video_width, video_height))
            background_clip = apply_blur(background_clip, blur_radius=70)
            # 缩放原始片段高度一致
            split_clip = split_clip.resize(height=video_height)
            split_clip = split_clip.set_position(("center", "center"))
            split_clip = CompositeVideoClip([background_clip, split_clip])

        # 设置前面片段的音量与后续一致
        split_clip = split_clip.volumex(params.voice_volume)

        # 在前面的视频片段上添加标题文本
        title_text_clip = create_text_clip(title, split_clip.duration, 0)
        split_clip = CompositeVideoClip([split_clip, title_text_clip])

        # 在前面的片段上应用声音淡出效果
        fadeout_duration = 1  # 1秒的声音淡出效果
        split_clip = split_clip.audio_fadeout(fadeout_duration)

        # 拼接前面的视频片段
        logger.info(" # 拼接前面的视频片段 split_clip")
        final_clip = concatenate_videoclips([split_clip, combined_video_clip])
        logger.info(f"在视频开头拼接 split_video_paths 中的第一个视频片段，时长 {split_clip.duration} 秒")
    else:
        final_clip = combined_video_clip

    # 最后再拼接 title_clip
    final_clip = concatenate_videoclips([title_clip, final_clip])

    write_start_time = time.time()
    await write_videofile_async(final_clip, filename=output_file, audio_codec="aac", temp_audiofile_path=output_dir,
                                logger=None, fps=30)
    final_clip.close()
    logger.success(f"写入视频文件耗时: {time.time() - write_start_time:.2f} 秒")
    logger.success(f"生成视频总耗时: {time.time() - start_timestamp:.2f} 秒")

    # 确保所有打开的资源都关闭
    combined_video_clip.close()
    audio_clip.close()
    title_clip.close()
    if 'bgm_clip' in locals():
        bgm_clip.close()
    if 'split_clip' in locals():
        split_clip.close()
    if 'text_clips' in locals():
        for clip in text_clips:
            clip.close()
    final_clip.close()

    loop = asyncio.get_event_loop()
    frame = await loop.run_in_executor(executor, lambda: VideoFileClip(output_file).get_frame(0))
    cover_image_path = os.path.join(utils.task_dir(), task_id, "cover.png")
    image = Image.fromarray(frame)
    await loop.run_in_executor(executor, image.save, cover_image_path)

    logger.success("封面图片已保存", cover_image_path)
    draft.add_material("cover", {"path": cover_image_path,
                                 "cover_mode": cover_mode,
                                 "text": title})


async def add_image_clips(image_paths, video_width, video_height, clip_duration):
    image_clips = []
    loop = asyncio.get_event_loop()
    for image_path in image_paths:
        img_clip = await loop.run_in_executor(executor, ImageClip, image_path)
        img_clip = img_clip.resize(height=video_height * 0.9)
        img_clip = img_clip.set_position(("center", "center"))
        img_clip = img_clip.set_duration(clip_duration).fadeout(1).resize(lambda t: 1 + 0.03 * t)
        image_clips.append(img_clip)

    return image_clips


async def get_duration(video_path):
    try:
        with VideoFileClip(video_path) as video:
            return video.duration
    except Exception as e:
        logger.error(f"Failed to get duration for video {video_path}: {str(e)}")
        return 0


def wrap_text(text, max_width, font="Arial", fontsize=60):
    font = ImageFont.truetype(font, fontsize)

    def get_text_size(inner_text):
        inner_text = inner_text.strip()
        left, top, right, bottom = font.getbbox(inner_text)
        return right - left, bottom - top

    width, height = get_text_size(text)
    if width <= max_width:
        return text, height

    processed = True
    _wrapped_lines_ = []
    words = text.split(" ")
    _txt_ = ""
    for word in words:
        _before = _txt_
        _txt_ += f"{word} "
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            if _txt_.strip() == word.strip():
                processed = False
                break
            _wrapped_lines_.append(_before)
            _txt_ = f"{word} "
    _wrapped_lines_.append(_txt_)
    if processed:
        _wrapped_lines_ = [line.strip() for line in _wrapped_lines_]
        result = "\n".join(_wrapped_lines_).strip()
        height = len(_wrapped_lines_) * height
        return result, height

    _wrapped_lines_ = []
    chars = list(text)
    _txt_ = ""
    for word in chars:
        _txt_ += word
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            _wrapped_lines_.append(_txt_)
            _txt_ = ""
    _wrapped_lines_.append(_txt_)
    result = "\n".join(_wrapped_lines_).strip()
    height = len(_wrapped_lines_) * height
    return result, height
