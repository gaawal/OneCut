import platform
import asyncio
import multiprocessing
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from PIL import Image, ImageFont
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
        audio_duration = 60.1
        logger.info(f"调整视频总时长为 {audio_duration}（秒）")
    req_dur = audio_duration / len(video_paths)
    req_dur = max_clip_duration
    logger.info(f"单个视频素材片段最大时长 {req_dur}（秒）")
    output_dir = os.path.dirname(combined_video_path)
    aspect = VideoAspect(video_aspect)
    video_width, video_height = aspect.to_resolution()

    clips = []
    video_duration = 0

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
            # Check clip resolution
            if (split_clip.w == video_width) and (split_clip.h == video_height):
                raw_clips.append(split_clip)
            else:
                logger.info(
                    f"Skipping clip with resolution {split_clip.w}x{split_clip.h}, expected {video_width}x{video_height}")
            start_time = end_time
            if video_concat_mode == VideoConcatMode.sequential:
                break
    logger.info(f"原始片段准备耗时: {time.time() - raw_clips_start_time:.2f} 秒")

    if video_concat_mode == VideoConcatMode.random:
        random.shuffle(raw_clips)

    resize_start_time = time.time()
    resized_clips = await asyncio.gather(
        *(resize_clip_async(clip, video_width, video_height) for clip in raw_clips))
    logger.info(f"调整视频片段尺寸耗时: {time.time() - resize_start_time:.2f} 秒")

    if images_files:
        image_clips = await add_image_clips(images_files, video_width, video_height, clip_duration=max_clip_duration)
        composite_clips = []
        for i, clip in enumerate(resized_clips):
            img_clip = image_clips[i % len(image_clips)]
            composite_clip = CompositeVideoClip([clip, img_clip])
            composite_clips.append(composite_clip)
        resized_clips = composite_clips

    while video_duration < audio_duration:
        for clip in resized_clips:
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
    for clip in resized_clips:
        clip.close()
    video_clip.close()
    audio_clip.close()

    logger.success(f"写入视频文件耗时: {time.time() - write_start_time:.2f} 秒")
    logger.success(f"合并视频总耗时: {time.time() - start_timestamp:.2f} 秒")

    return combined_video_path


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


async def generate_video(task_id, title, video_path, images_path, audio_path, bgm_path, subtitle_path, output_file,
                         params, draft):
    start_time = datetime.now()
    start_timestamp = time.time()
    logger.info(f"开始生成视频任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    aspect = VideoAspect(params.video_aspect)
    video_width, video_height = aspect.to_resolution()

    logger.info(f"开始生成视频，视频尺寸: {video_width} x {video_height}")
    logger.info(f"  ① 视频文件: {video_path}")
    logger.info(f"  ② 人声文件: {audio_path}")
    logger.info(f"  ③ 背景音乐: {bgm_path}")
    logger.info(f"  ④ 字幕文件: {subtitle_path}")
    logger.info(f"  ⑤ 目标输出视频: {output_file}")
    output_dir = os.path.dirname(output_file)

    font_path = get_font_path(params)

    cover_mode = "video_frame"
    random_bg = True
    title_clip = create_title_clip(params, title, video_width, video_height, images_path, font_path,
                                   video_path=video_path,
                                   cover_mode=cover_mode, random_bg=random_bg)

    def create_text_clip(subtitle_item):
        phrase = subtitle_item[1]
        max_width = video_width * 0.9
        wrapped_txt, txt_height = wrap_text(phrase, max_width=max_width, font=font_path, fontsize=params.font_size)

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

        duration = subtitle_item[0][1] - subtitle_item[0][0]
        _clip = _clip.set_start(subtitle_item[0][0])
        _clip = _clip.set_end(subtitle_item[0][1])
        _clip = _clip.set_duration(duration)

        if params.subtitle_position == "bottom":
            _clip = _clip.set_position(("center", video_height * 0.95 - _clip.h))
        elif params.subtitle_position == "top":
            _clip = _clip.set_position(("center", video_height * 0.1))
        else:
            _clip = _clip.set_position(("center", "center"))

        return _clip

    video_clip = await create_video_clip_async(video_path)
    audio_clip = await create_audio_clip_async(audio_path)
    audio_clip = audio_clip.volumex(params.voice_volume)

    if subtitle_path and os.path.exists(subtitle_path):
        sub = SubtitlesClip(subtitles=subtitle_path, encoding="utf-8")
        text_clips = [create_text_clip(item) for item in sub.subtitles]
        video_clip = CompositeVideoClip([video_clip, *text_clips])

    if bgm_path:
        try:
            bgm_clip = await create_audio_clip_async(bgm_path)
            bgm_clip = bgm_clip.volumex(params.bgm_volume).audio_fadeout(3)
            bgm_clip = afx.audio_loop(bgm_clip, duration=video_clip.duration)
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"failed to add bgm: {str(e)}")

    video_clip = video_clip.set_audio(audio_clip)
    final_clip = concatenate_videoclips([title_clip, video_clip])

    write_start_time = time.time()
    await write_videofile_async(final_clip, filename=output_file, audio_codec="aac", temp_audiofile_path=output_dir,
                                logger=None, fps=30)
    final_clip.close()
    logger.success(f"写入视频文件耗时: {time.time() - write_start_time:.2f} 秒")
    logger.success(f"生成视频总耗时: {time.time() - start_timestamp:.2f} 秒")

    # 确保所有打开的资源都关闭
    video_clip.close()
    audio_clip.close()
    if 'bgm_clip' in locals():
        bgm_clip.close()
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
                                 "text": title
                                 }
                       )


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