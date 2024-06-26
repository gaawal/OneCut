import math
import os.path
import traceback
from os import path

from loguru import logger

from app.models.constant import TaskState, SubtitleProvider, TaskDetailState, TaskFailureReason
from app.settings import movies_config
from app.schemas.movies import VideoParams, VideoConcatMode, TaskProgress
from app.services import llm, material, voice, video, subtitle
from app.utils import utils


def start(task_id, redis_state, params: VideoParams):
    logger.info(f"start task: {task_id}")
    task_progress = TaskProgress()
    try:
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=5,
                                detail_state=TaskDetailState.GENERATING_SCRIPT)

        # 生成视频文案信息
        video_script, video_terms, video_title = generate_video_script_and_terms(params)
        if not video_script:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_SCRIPT)
            return
        if not video_terms:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_SCRIPT)
            return
        if not video_title:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_SCRIPT)
            return

        task_progress.script = video_script
        task_progress.video_title = video_title
        task_progress.search_terms = video_terms
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=10,
                                detail_state=TaskDetailState.SCRIPT_GENERATION_COMPLETE,
                                **task_progress.model_dump())

        # 保存文案配置
        save_script(task_id, video_script, video_terms, params)

        # 生成音频
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=20,
                                detail_state=TaskDetailState.GENERATING_AUDIO)
        audio_file, audio_duration, sub_maker = generate_audio(task_id, params, video_script,
                                                               voice_name=params.voice_name)
        if not audio_file:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_AUDIO)
            return

        task_progress.audio_file = audio_file
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=30,
                                detail_state=TaskDetailState.AUDIO_GENERATION_COMPLETE,
                                **task_progress.model_dump())

        # 生成字幕
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=40,
                                detail_state=TaskDetailState.GENERATING_SUBTITLE)
        subtitle_path = generate_subtitle(task_id, params, audio_file, video_script, sub_maker)
        task_progress.subtitle_file = subtitle_path
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=50,
                                detail_state=TaskDetailState.SUBTITLE_GENERATION_COMPLETE,
                                **task_progress.model_dump())

        # 下载视频
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=60,
                                detail_state=TaskDetailState.DOWNLOADING_VIDEOS)
        downloaded_videos = download_videos(task_id, params, video_terms, audio_duration, redis_state)
        if not downloaded_videos:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_DOWNLOADING_VIDEOS)
            return

        task_progress.downloaded_videos = downloaded_videos
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=70,
                                detail_state=TaskDetailState.VIDEO_DOWNLOAD_COMPLETE,
                                **task_progress.model_dump())

        # 合并和生成最终视频
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=80,
                                detail_state=TaskDetailState.COMBINING_VIDEOS)
        final_video_paths = combine_and_generate_videos(task_id, params, downloaded_videos, audio_file, subtitle_path,
                                                        task_progress, redis_state)
        if not final_video_paths:
            redis_state.update_task(task_id, state=TaskState.FAILED,
                                    failure_reason=TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO)
            return

        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=90,
                                detail_state=TaskDetailState.COMBINED_VIDEOS_COMPLETE,
                                **task_progress.model_dump())
        redis_state.update_task(task_id, state=TaskState.PROCESSING, progress=95,
                                detail_state=TaskDetailState.GENERATING_FINAL_VIDEO)

        logger.success(f"task {task_id} finished, generated {len(final_video_paths)} videos.")
        redis_state.update_task(task_id, state=TaskState.COMPLETE, progress=100,
                                detail_state=TaskDetailState.FINAL_VIDEO_GENERATION_COMPLETE,
                                **task_progress.model_dump())
    except ValueError as e:
        logger.error(f"task failed: {task_id} cause by {traceback.format_exc()}")
        failure_reason = TaskFailureReason.VALUE_ERROR  # default failure reason, can be adjusted
        redis_state.update_task(task_id, state=TaskState.FAILED, progress=100, failure_reason=failure_reason,
                                error=str(e), **task_progress.model_dump())
    except Exception as e:
        logger.error(f"task failed: {task_id} cause by {traceback.format_exc()}")
        failure_reason = TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO  # default failure reason, can be adjusted
        redis_state.update_task(task_id, state=TaskState.FAILED, progress=100, failure_reason=failure_reason,
                                error=str(e), **task_progress.model_dump())
    return task_progress.model_dump()


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
                                                                               amount=params.amount,word_count=params.word_count)


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


def generate_audio(task_id, params, video_script, voice_name):
    logger.info("\n\n## generating audio")
    audio_file = path.join(utils.task_dir(task_id), f"audio.mp3")
    sub_maker = voice.tts(text=video_script, voice_name=voice_name, voice_file=audio_file)
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


def generate_subtitle(task_id, params, audio_file, video_script, sub_maker):
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


def download_videos(task_id, params, video_terms, audio_duration, redis_state):
    downloaded_videos = []
    if params.video_source == "local":
        logger.info("\n\n## preprocess local materials")
        materials = video.preprocess_video(materials=params.video_materials, clip_duration=params.video_clip_duration)
        if not materials:
            logger.error("no valid materials found, please check the materials and try again.")
            return None
        for material_info in materials:
            downloaded_videos.append(material_info.url)
    else:
        logger.info(f"\n\n## downloading videos from {params.video_source}")
        downloaded_videos = material.download_videos(task_id=task_id,
                                                     search_terms=video_terms,
                                                     source=params.video_source,
                                                     video_aspect=params.video_aspect,
                                                     video_contact_mode=params.video_concat_mode,
                                                     audio_duration=audio_duration * params.video_count,
                                                     max_clip_duration=params.video_clip_duration,
                                                     redis_state=redis_state)
    if not downloaded_videos:
        logger.error(
            "failed to download videos, maybe the network is not available. if you are in China, please use a VPN.")
        return None

    return downloaded_videos


def combine_and_generate_videos(task_id, params, downloaded_videos, audio_file, subtitle_path, task_progress,
                                redis_state):
    video_concat_mode = params.video_concat_mode
    if params.video_count > 1:
        video_concat_mode = VideoConcatMode.random

    _progress = 80
    for i in range(params.video_count):
        index = i + 1
        combined_video_path = path.join(utils.task_dir(task_id), f"combined-{index}.mp4")
        logger.info(f"\n\n## combining video: {index} => {combined_video_path}")
        video.combine_videos(combined_video_path=combined_video_path,
                             video_paths=downloaded_videos,
                             audio_file=audio_file,
                             video_aspect=params.video_aspect,
                             video_concat_mode=video_concat_mode,
                             max_clip_duration=params.video_clip_duration,
                             threads=params.n_threads)

        _progress += 50 / params.video_count / 2
        task_progress.combined_videos.append(combined_video_path)
        redis_state.update_task(task_id, progress=_progress, **task_progress.model_dump())

        final_video_path = path.join(utils.task_dir(task_id), f"final-{index}.mp4")

        logger.info(f"\n\n## generating video: {index} => {final_video_path}")
        video.generate_video(video_path=combined_video_path,
                             audio_path=audio_file,
                             subtitle_path=subtitle_path,
                             output_file=final_video_path,
                             params=params,
                             )

        _progress += 50 / params.video_count / 2
        task_progress.final_videos.append(final_video_path)
        redis_state.update_task(task_id, progress=_progress, **task_progress.model_dump())

    return task_progress.final_videos
