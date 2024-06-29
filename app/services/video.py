import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from PIL import ImageFont
from fastapi import Request
from loguru import logger
from moviepy.editor import *
from moviepy.video.fx.resize import resize
from moviepy.video.tools.subtitles import SubtitlesClip
from app.schemas.movies import VideoAspect, VideoParams, VideoConcatMode
from app.services.redis_service import RedisService
from app.utils import utils


async def get_bgm_file(request: Request, bgm_type: str = "random", bgm_file: str = ""):
    logger.info(f"get bgm file,bgm_type is {bgm_type},bgm_file is {bgm_file}")
    suffix = ".mp3"
    choose_bgm_file = ''
    song_dir = utils.song_dir()
    redis_service = RedisService(request.app.state.redis)
    if bgm_type == "random":
        cache_key = "bgm_list_cache"
        cached_data = await redis_service.get(cache_key)
        if cached_data:
            logger.success(f'get bgm list in redis cache ok,try to random choice it')
            response = json.loads(cached_data)
            files = response.get("files")
            random_file_info = random.choice(files)
            genres = random_file_info.get('genres')
            name = random_file_info.get('name')
            choose_bgm_file = os.path.join(song_dir, genres, name)
            logger.info(f'random choice bgm file is {choose_bgm_file}')
    else:
        bgm_file_key = 'bgm_file_cache:'
        cache_bgm_key = (f"{bgm_file_key}{bgm_file}{suffix}")
        if not bgm_type:
            logger.warning(f"get bgm file failed,{bgm_file} is not available")
            return ""
        cached_data = await redis_service.get(cache_bgm_key)
        if cached_data:
            logger.success(f'get bgm in redis cache ok,redis key is {cache_bgm_key}')
            bgm_info = json.loads(cached_data)
            genres = bgm_info.get('genres')
            name = bgm_info.get('name')
            choose_bgm_file = os.path.join(song_dir, genres, name)
        else:
            logger.warning(f'No bgm in redis cache,redis key is {cache_bgm_key}')
    if not choose_bgm_file and not os.path.exists(choose_bgm_file):
        logger.info(f'No bgm in file in path {choose_bgm_file}')

    return choose_bgm_file


def resize_clip(clip, video_width, video_height):
    clip_w, clip_h = clip.size
    if clip_w != video_width or clip_h != video_height:
        clip_ratio = clip_w / clip_h
        video_ratio = video_width / video_height

        if clip_ratio == video_ratio:
            # 等比例缩放
            clip = resize(clip, (video_width, video_height))
        else:
            # 等比缩放视频
            if clip_ratio > video_ratio:
                # 按照目标宽度等比缩放
                scale_factor = video_width / clip_w
            else:
                # 按照目标高度等比缩放
                scale_factor = video_height / clip_h

            new_width = int(clip_w * scale_factor)
            new_height = int(clip_h * scale_factor)
            clip_resized = resize(clip, newsize=(new_width, new_height))

            background = ColorClip(size=(video_width, video_height), color=(0, 0, 0))
            clip = CompositeVideoClip([
                background.set_duration(clip.duration),
                clip_resized.set_position("center")
            ])
        logger.info(f"resizing video to {video_width} x {video_height}, clip size: {clip_w} x {clip_h}")
    return clip


def combine_videos(combined_video_path: str,
                   video_paths: List[str],
                   audio_file: str,
                   video_aspect: VideoAspect = VideoAspect.portrait,
                   video_concat_mode: VideoConcatMode = VideoConcatMode.random,
                   max_clip_duration: int = 5,
                   threads: int = 2,
                   ) -> str:
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration
    logger.info(f"max duration of audio: {audio_duration} seconds")
    # Required duration of each clip
    req_dur = audio_duration / len(video_paths)
    req_dur = max_clip_duration
    logger.info(f"each clip will be maximum {req_dur} seconds long")
    output_dir = os.path.dirname(combined_video_path)

    aspect = VideoAspect(video_aspect)
    video_width, video_height = aspect.to_resolution()

    clips = []
    video_duration = 0

    raw_clips = []
    for video_path in video_paths:
        cache_dir = utils.cache_videos_dir()
        video_file = os.path.join(cache_dir, f"{video_path}")
        clip = VideoFileClip(video_file).without_audio()
        clip_duration = clip.duration
        start_time = 0

        while start_time < clip_duration:
            end_time = min(start_time + max_clip_duration, clip_duration)
            split_clip = clip.subclip(start_time, end_time)
            raw_clips.append(split_clip)
            start_time = end_time
            if video_concat_mode.value == VideoConcatMode.sequential.value:
                break

    if video_concat_mode.value == VideoConcatMode.random.value:
        random.shuffle(raw_clips)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(resize_clip, clip, video_width, video_height) for clip in raw_clips]
        resized_clips = [future.result() for future in as_completed(futures)]

    while video_duration < audio_duration:
        for clip in resized_clips:
            if (audio_duration - video_duration) < clip.duration:
                clip = clip.subclip(0, (audio_duration - video_duration))
            elif req_dur < clip.duration:
                clip = clip.subclip(0, req_dur)
            clip = clip.set_fps(30)

            clips.append(clip)
            video_duration += clip.duration

    video_clip = concatenate_videoclips(clips)
    video_clip = video_clip.set_fps(30)
    logger.info(f"combined video clip")
    video_clip.write_videofile(filename=combined_video_path,
                               threads=threads,
                               logger=None,
                               temp_audiofile_path=output_dir,
                               audio_codec="aac",
                               fps=30,
                               )
    video_clip.close()
    logger.success(f"combined video completed")
    return combined_video_path


def wrap_text(text, max_width, font='Arial', fontsize=60):
    # 创建字体对象
    font = ImageFont.truetype(font, fontsize)

    def get_text_size(inner_text):
        inner_text = inner_text.strip()
        left, top, right, bottom = font.getbbox(inner_text)
        return right - left, bottom - top

    width, height = get_text_size(text)
    if width <= max_width:
        return text, height

    # logger.warning(f"wrapping text, max_width: {max_width}, text_width: {width}, text: {text}")

    processed = True

    _wrapped_lines_ = []
    words = text.split(" ")
    _txt_ = ''
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
        result = '\n'.join(_wrapped_lines_).strip()
        height = len(_wrapped_lines_) * height
        # logger.warning(f"wrapped text: {result}")
        return result, height

    _wrapped_lines_ = []
    chars = list(text)
    _txt_ = ''
    for word in chars:
        _txt_ += word
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            _wrapped_lines_.append(_txt_)
            _txt_ = ''
    _wrapped_lines_.append(_txt_)
    result = '\n'.join(_wrapped_lines_).strip()
    height = len(_wrapped_lines_) * height
    return result, height


def generate_video(video_path: str,
                   audio_path: str,
                   bgm_path: str,
                   subtitle_path: str,
                   output_file: str,
                   params: VideoParams,
                   ):
    aspect = VideoAspect(params.video_aspect)
    video_width, video_height = aspect.to_resolution()

    logger.info(f"start, video size: {video_width} x {video_height}")
    logger.info(f"  ① video: {video_path}")
    logger.info(f"  ② audio: {audio_path}")
    logger.info(f"  ③ bgm: {bgm_path}")
    logger.info(f"  ④ subtitle: {subtitle_path}")
    logger.info(f"  ⑤ output: {output_file}")

    # https://github.com/harry0703/MoneyPrinterTurbo/issues/217
    # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'final-1.mp4.tempTEMP_MPY_wvf_snd.mp3'
    # write into the same directory as the output file
    output_dir = os.path.dirname(output_file)

    font_path = ""
    if params.subtitle_enabled:
        if not params.font_name:
            params.font_name = "STHeitiMedium.ttc"
        font_path = os.path.join(utils.font_dir(), params.font_name)
        if os.name == 'nt':
            font_path = font_path.replace("\\", "/")

        logger.info(f"using font: {font_path}")

    def create_text_clip(subtitle_item):
        phrase = subtitle_item[1]
        max_width = video_width * 0.9
        wrapped_txt, txt_height = wrap_text(phrase,
                                            max_width=max_width,
                                            font=font_path,
                                            fontsize=params.font_size
                                            )
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
            _clip = _clip.set_position(('center', video_height * 0.95 - _clip.h))
        elif params.subtitle_position == "top":
            _clip = _clip.set_position(('center', video_height * 0.1))
        else:
            _clip = _clip.set_position(('center', 'center'))
        return _clip

    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path).volumex(params.voice_volume)

    if subtitle_path and os.path.exists(subtitle_path):
        sub = SubtitlesClip(subtitles=subtitle_path, encoding='utf-8')
        text_clips = []
        for item in sub.subtitles:
            clip = create_text_clip(subtitle_item=item)
            text_clips.append(clip)
        video_clip = CompositeVideoClip([video_clip, *text_clips])

    if bgm_path:
        try:
            bgm_clip = (AudioFileClip(bgm_path)
                        .volumex(params.bgm_volume)
                        .audio_fadeout(3))
            bgm_clip = afx.audio_loop(bgm_clip, duration=video_clip.duration)
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"failed to add bgm: {str(e)}")

    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_file,
                               audio_codec="aac",
                               temp_audiofile_path=output_dir,
                               threads=params.n_threads or 2,
                               logger=None,
                               fps=30,
                               )
    video_clip.close()
    logger.success(f"task completed")

