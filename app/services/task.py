import asyncio
import json
import math
import os.path
import os.path
import time
import traceback
from os import path

from loguru import logger
from fastapi import Request
from app.models.constant import TaskState, SubtitleProvider, TaskDetailState, TaskFailureReason
from app.schemas.movies import VideoParams, VideoConcatMode, TaskProgress
from app.services import llm, material, voice, video, subtitle
from app.services.video import get_bgm_file
from app.settings import movies_config
from app.utils import utils
from app.utils.utils import calculate_duration


async def start(task_id, redis_state, params: VideoParams, request: Request):
    start_time = time.time()
    logger.info(f"start task: {task_id}")
    task_progress = TaskProgress()
    try:
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=5,
                                detail_state=TaskDetailState.GENERATING_SCRIPT)
        # 生成视频文案信息
        video_script, video_terms, video_title = generate_video_script_and_terms(params)
        if not all([video_script, video_terms, video_title]):
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_SCRIPT)
            return

        task_progress.script = video_script
        task_progress.video_title = video_title
        task_progress.search_terms = video_terms
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=10,
                                detail_state=TaskDetailState.SCRIPT_GENERATION_COMPLETE, **task_progress.dict())

        save_script(task_id, video_script, video_terms, params)

        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=20,
                                detail_state=TaskDetailState.GENERATING_AUDIO)
        audio_file, audio_duration, sub_maker = await generate_audio(task_id, params, video_script, params.voice_name)
        if not audio_file:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_AUDIO)
            return

        task_progress.audio_file = audio_file
        task_progress.audio_duration = audio_duration
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=30,
                                detail_state=TaskDetailState.AUDIO_GENERATION_COMPLETE, **task_progress.dict())
        # 并行执行加入背景音乐、生成字幕和下载视频
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=40,
                                detail_state=TaskDetailState.GENERATING_SUBTITLE)
        subtitle_future = asyncio.create_task(generate_subtitle(task_id, params, audio_file, video_script, sub_maker))
        bgmfile_future = asyncio.create_task(
            get_bgm_file(request=request, bgm_type=params.bgm_type, bgm_file=params.bgm_file))
        bgm_path = await bgmfile_future
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=50,
                                detail_state=TaskDetailState.DOWNLOADING_VIDEOS)

        download_videos_future = asyncio.create_task(
            material.download_videos(task_id, video_terms, params.video_source, params.video_aspect,
                                     params.video_concat_mode, audio_duration, params.video_clip_duration, redis_state))

        subtitle_path = await subtitle_future
        if not subtitle_path:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_SUBTITLE)
            return

        downloaded_videos = await download_videos_future
        if not downloaded_videos:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_DOWNLOADING_VIDEOS)
            return

        task_progress.subtitle_file = subtitle_path
        task_progress.downloaded_videos = downloaded_videos
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=70,
                                detail_state=TaskDetailState.VIDEO_DOWNLOAD_COMPLETE, **task_progress.dict())

        # 合并视频
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=80,
                                detail_state=TaskDetailState.COMBINING_VIDEOS)
        combined_video_path = await combine_videos(task_id, params, downloaded_videos, audio_file, task_progress,
                                                   redis_state)
        if not combined_video_path:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO)
            return

        task_progress.combined_videos = combined_video_path
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=90,
                                detail_state=TaskDetailState.COMBINED_VIDEOS_COMPLETE, **task_progress.dict())

        # 生成最终视频
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=95,
                                detail_state=TaskDetailState.GENERATING_FINAL_VIDEO)

        final_video_path = await generate_final_video(task_id, params, combined_video_path, audio_file, bgm_path,
                                                      subtitle_path, task_progress, redis_state)
        if not final_video_path:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO)
            return

        task_progress.final_videos = final_video_path
        redis_state.update_task(task_id, state=TaskState.COMPLETE, progress=100,
                                detail_state=TaskDetailState.FINAL_VIDEO_GENERATION_COMPLETE, **task_progress.dict())

        logger.success(f"task {task_id} finished, generated final video: {final_video_path}.")
    except ValueError as e:
        logger.error(f"task failed: {task_id} cause by {traceback.format_exc()}")
        redis_state.update_task(task_id, state=TaskState.FAILED, progress=100,
                                failure_reason=TaskFailureReason.VALUE_ERROR, error=str(e), **task_progress.dict())
    except Exception as e:
        logger.error(f"task failed: {task_id} cause by {traceback.format_exc()}")
        redis_state.update_task(task_id, state=TaskState.FAILED, progress=100,
                                failure_reason=TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO, error=str(e),
                                **task_progress.dict())
    end_time = time.time()
    minutes, seconds = calculate_duration(start_time, end_time)
    logger.info(f"使用时长为：{minutes} 分钟 {seconds} 秒")
    return task_progress.dict()


async def combine_videos(task_id, params, downloaded_videos, audio_file, task_progress, redis_state):
    combined_video_path = []
    video_concat_mode = params.video_concat_mode
    if params.video_count > 1:
        video_concat_mode = VideoConcatMode.random

    _progress = 80
    progress_increment = 10 / params.video_count  # Adjusting progress increment for 80 to 90 range
    for i in range(params.video_count):
        index = i + 1
        combined_video = path.join(utils.task_dir(task_id), f"combined-{index}.mp4")
        logger.info(f"\n\n## combining video: {index} => {combined_video}")
        video.combine_videos(combined_video_path=combined_video,
                             video_paths=downloaded_videos,
                             audio_file=audio_file,
                             video_aspect=params.video_aspect,
                             video_concat_mode=video_concat_mode,
                             max_clip_duration=params.video_clip_duration,
                             threads=params.n_threads)

        _progress += progress_increment
        task_progress.combined_videos.append(combined_video)
        redis_state.update_task(task_id, progress=_progress, **task_progress.dict())

        combined_video_path.append(combined_video)

    return combined_video_path


async def generate_final_video(task_id, params, combined_video_path, audio_file, bgm_file, subtitle_path, task_progress,
                               redis_state):
    final_video_paths = []
    _progress = 90

    for i, combined_video in enumerate(combined_video_path):
        final_video = path.join(utils.task_dir(task_id), f"final-{i + 1}.mp4")

        logger.info(f"\n\n## generating final video: {i + 1} => {final_video}")
        video.generate_video(video_path=combined_video,
                             audio_path=audio_file,
                             bgm_path=bgm_file,
                             subtitle_path=subtitle_path,
                             output_file=final_video,
                             params=params)

        _progress += 50 / len(combined_video_path) / 2
        task_progress.final_videos.append(final_video)
        redis_state.update_task(task_id, progress=_progress, **task_progress.dict())

        final_video_paths.append(final_video)

    return final_video_paths


def generate_video_script_and_terms(params):
    logger.info("\n\n## generating video script")
    video_script = params.video_script.strip()
    video_terms = params.video_terms
    video_title = params.video_subject
    if not video_script:
        video_script, video_terms, video_title = llm.generate_script_and_terms(video_subject=params.video_subject,
                                                                               language=params.video_language,
                                                                               paragraph_number=params.paragraph_number,
                                                                               video_category=params.video_category,
                                                                               amount=params.amount,
                                                                               word_count=params.word_count)
    else:
        logger.info("no need to generate video script.")
    return video_script, video_terms, video_title


def save_script(task_id, video_script, video_terms, params):
    script_file = path.join(utils.task_dir(task_id), f"script.json")
    kwargs = {
        "script": video_script,
        "search_terms": video_terms,
        "params": params,
    }

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(utils.to_json(kwargs))

    return script_file


async def generate_audio(task_id, params, video_script, voice_name):
    logger.info("\n\n## generating audio")
    audio_file = path.join(utils.task_dir(task_id), f"audio.mp3")
    sub_maker = await voice.tts(text=video_script, voice_name=voice_name, voice_file=audio_file)
    if sub_maker is None:
        logger.error(
            """failed to generate audio:
1. check if the language of the voice matches the language of the video script.
2. check if the network is available. If you are in China, it is recommended to use a VPN and enable the global traffic mode.
        """.strip()
        )
        return None, None, None

    audio_duration = voice.get_audio_duration(sub_maker)
    audio_duration = math.ceil(audio_duration)

    return audio_file, audio_duration, sub_maker


async def generate_subtitle(task_id, params, audio_file, video_script, sub_maker):
    subtitle_path = ""
    if params.subtitle_enabled:
        subtitle_path = path.join(utils.task_dir(task_id), f"subtitle.srt")
        subtitle_provider = movies_config.app.get("subtitle_provider", "").strip().lower()
        logger.info(f"\n\n## generating subtitle, provider: {subtitle_provider}")
        subtitle_fallback = False
        if subtitle_provider == SubtitleProvider.EDGE:
            voice.create_subtitle(text=video_script, sub_maker=sub_maker, subtitle_file=subtitle_path)
            if not os.path.exists(subtitle_path):
                subtitle_fallback = True
                logger.warning("subtitle file not found, fallback to whisper")

        if subtitle_provider == SubtitleProvider.WHISPER or subtitle_fallback:
            subtitle.create(audio_file=audio_file, subtitle_file=subtitle_path)
            logger.info("\n\n## correcting subtitle")
            subtitle.correct(subtitle_file=subtitle_path, video_script=video_script)

        subtitle_lines = subtitle.file_to_subtitles(subtitle_path)
        if not subtitle_lines:
            logger.warning(f"subtitle file is invalid: {subtitle_path}")
            subtitle_path = ""

    return subtitle_path


def generate_draft(task_id, task_progress, params):
    draft = {
        "canvas_config": {
            "height": params.video_height,
            "ratio": "original",
            "width": params.video_width
        },
        "color_space": 0,
        "config": {
            "adjust_max_index": 1,
            "attachment_info": [],
            "combination_max_index": 1,
            "export_range": None,
            "extract_audio_last_index": 1,
            "lyrics_recognition_id": "",
            "lyrics_sync": True,
            "lyrics_taskinfo": [],
            "maintrack_adsorb": True,
            "material_save_mode": 0,
            "original_sound_last_index": 1,
            "record_audio_last_index": 1,
            "sticker_max_index": 1,
            "subtitle_recognition_id": "",
            "subtitle_sync": True,
            "subtitle_taskinfo": [],
            "video_mute": False,
            "zoom_info_params": None
        },
        "cover": None,
        "create_time": 0,
        "duration": task_progress.total_duration,
        "extra_info": None,
        "fps": 30.0,
        "free_render_index_mode_on": False,
        "group_container": None,
        "id": task_id,
        "keyframes": {
            "adjusts": [],
            "audios": [],
            "filters": [],
            "handwrites": [],
            "stickers": [],
            "texts": [],
            "videos": []
        },
        "last_modified_platform": {
            "app_id": 3704,
            "app_source": "lv",
            "app_version": "3.8.0",
            "device_id": "4897f4afa676f10850f610dfdaf6dd0d",
            "hard_disk_id": "9eb2dee2aa32fa72694c5cf4d70451f4",
            "mac_address": "64ac16c2f5d9546cadc7c8c98740aa9b",
            "os": "mac",
            "os_version": "12.5.1"
        },
        "materials": {
            "audio_fades": [],
            "audios": [
                {
                    "id": task_progress.audio_file,
                    "duration": task_progress.audio_duration,
                    "path": task_progress.audio_file,
                    "name": params.audio_name,
                    "type": "audio"
                }
            ],
            "videos": [
                {
                    "id": video,
                    "path": video,
                    "duration": video_duration,
                    "type": "video"
                } for video, video_duration in zip(task_progress.downloaded_videos, params.video_durations)
            ],
            "subtitles": [
                {
                    "id": task_progress.subtitle_file,
                    "path": task_progress.subtitle_file,
                    "type": "subtitle"
                }
            ]
        },
        "update_time": 0,
        "version": "1.0"
    }
    with open(f"{utils.task_dir(task_id)}/draft.json", "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=4)
