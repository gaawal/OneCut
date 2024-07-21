import os
import time
import traceback
from os import path

from fastapi import Request
from loguru import logger

from app.constant.video_const import TaskState, TaskDetailState, TaskFailureReason
from app.core.ctx import CTX_USER_ID
from app.schemas.drafts import Draft
from app.schemas.movies import VideoParams, VideoConcatMode, TaskProgress
from app.services.factory import llm_generator, material_generator, subtitle_generator, video_generator, \
    voice_generator, images_generator, audio_generator
from app.utils import utils
from app.utils.utils import calculate_duration
from app.services.redis_service import redis_instance
from app.controllers.video_task import task_controller
from app.schemas.video_task import TaskCreate, TaskUpdate
import warnings

# 忽略 moviepy 模块中的 UserWarning 警告
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")


async def start(task_id, params: VideoParams, request: Request):
    start_time = time.time()
    logger.info(f"start task: {task_id}")
    task_progress = TaskProgress()
    user_id = CTX_USER_ID.get()

    # 初始化任务记录
    task_in = TaskCreate(
        user_id=user_id,
        task_id=task_id,
        progress=0,
        state=TaskState.PROCESSING,
        draft_content={}
    )
    await task_controller.create(obj_in=task_in)

    # 尝试加载草稿
    draft_file = os.path.join(utils.task_dir(task_id), "draft.json")
    draft = Draft(task_id, params)
    if os.path.exists(draft_file):
        logger.info(f"Loading draft for task: {task_id}")
        draft.load_from_file(draft_file)
        # 根据草稿恢复任务状态和相关参数
        task_progress = restore_task_progress_from_draft(draft)
        await save_task_state(task_id, TaskState.PROCESSING, 50, TaskDetailState.LOADING_DRAFT, draft)
    else:
        draft = Draft(task_id, params)

    try:
        if not os.path.exists(draft_file):
            await save_task_state(task_id, TaskState.PROCESSING, 5, TaskDetailState.GENERATING_SCRIPT, draft)
            video_script, video_terms, video_title = llm_generator.generate_video_script_and_terms(params)
            if not all([video_script, video_terms, video_title]):
                await save_task_state(task_id, TaskState.FAILED, 5, TaskFailureReason.FAILED_GENERATING_SCRIPT, draft,
                                      TaskFailureReason.FAILED_GENERATING_SCRIPT)
                return

            task_progress.script = video_script
            task_progress.video_title = video_title
            task_progress.search_terms = video_terms
            await save_task_state(task_id, TaskState.PROCESSING, 10, TaskDetailState.SCRIPT_GENERATION_COMPLETE, draft,
                                  task_progress.dict())

            save_script(task_id, video_script, video_terms, params)

            # 更新草稿
            draft.add_script_info(video_script, video_terms, video_title)
            draft.save_to_file(utils.task_dir(task_id))

            await save_task_state(task_id, TaskState.PROCESSING, 15, TaskDetailState.GENERATING_AUDIO, draft)
            bgm_path = await audio_generator.get_bgm_file(request=request, bgm_type=params.bgm_type,
                                                          bgm_file=params.bgm_file)
            audio_file, audio_duration, sub_maker = await voice_generator.generate_audio(task_id, video_script,
                                                                                         params.voice_name)
            if not audio_file:
                await save_task_state(task_id, TaskState.FAILED, 16, TaskFailureReason.FAILED_GENERATING_AUDIO, draft,
                                      TaskFailureReason.FAILED_GENERATING_AUDIO)
                return

            task_progress.audio_file = audio_file
            task_progress.audio_duration = audio_duration
            await save_task_state(task_id, TaskState.PROCESSING, 20, TaskDetailState.AUDIO_GENERATION_COMPLETE, draft,
                                  task_progress.dict())

            draft.add_material("audios",
                               {"path": audio_file, "duration": audio_duration, "voice_name": params.voice_name})
            # 更新草稿

            draft.save_to_file(utils.task_dir(task_id))

            subtitle_path = await subtitle_generator.generate_subtitle(task_id, params, audio_file, video_script,
                                                                       sub_maker)

            images_files = await images_generator.get_images_files(request=request, params=params)
            await save_task_state(task_id, TaskState.PROCESSING, 50, TaskDetailState.DOWNLOADING_VIDEOS, draft)
            downloaded_videos = []
            if params.weibo_mid:
                logger.info("微博话题模式，视频素材从本地获取")
                downloaded_videos = material_generator.get_local_videos(audio_duration, params.video_clip_duration)
            if not downloaded_videos:
                logger.info("视频素材在线获取")
                downloaded_videos = await material_generator.download_videos(task_id, video_terms, params.video_source,
                                                                             params.video_aspect,
                                                                             params.video_concat_mode,
                                                                             audio_duration, params.video_clip_duration,
                                                                             draft,
                                                                             utils.task_dir(task_id))
            logger.info(f"视频素材文件为：{downloaded_videos}")
            if not subtitle_path:
                await save_task_state(task_id, TaskState.FAILED, 50, TaskFailureReason.FAILED_GENERATING_SUBTITLE,
                                      draft, TaskFailureReason.FAILED_GENERATING_SUBTITLE)
                return
            if not downloaded_videos:
                await save_task_state(task_id, TaskState.FAILED, 51, TaskFailureReason.FAILED_DOWNLOADING_VIDEOS, draft,
                                      TaskFailureReason.FAILED_DOWNLOADING_VIDEOS)
                return

            task_progress.images_files = images_files
            task_progress.bgm_file = subtitle_path
            task_progress.subtitle_file = subtitle_path
            task_progress.downloaded_videos = downloaded_videos
            await save_task_state(task_id, TaskState.PROCESSING, 60, TaskDetailState.VIDEO_DOWNLOAD_COMPLETE, draft,
                                  task_progress.dict())

            # 更新草稿
            draft.add_material("subtitles", {"path": subtitle_path})
            draft.add_material("images", [{"path": img, "start_time": i * 5, "duration": 5} for i, img in
                                          enumerate(images_files)])
            # 更新视频的保存
            draft.save_to_file(utils.task_dir(task_id))
        await save_task_state(task_id, TaskState.PROCESSING, 70, TaskDetailState.COMBINING_VIDEOS, draft)
        combined_video_path = await combine_videos(task_id, params, task_progress.downloaded_videos,
                                                   task_progress.audio_file, task_progress.images_files, task_progress,
                                                   draft)
        if not combined_video_path:
            await save_task_state(task_id, TaskState.FAILED, 71, TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO, draft,
                                  TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO)
            return
        task_progress.combined_videos = combined_video_path
        await save_task_state(task_id, TaskState.PROCESSING, 80, TaskDetailState.COMBINED_VIDEOS_COMPLETE, draft,
                              task_progress.dict())
        final_video_path = await generate_final_video(task_id, video_title, params, combined_video_path,images_files,
                                                      task_progress.audio_file,
                                                      bgm_path, subtitle_path, task_progress, draft)
        if not final_video_path:
            await save_task_state(task_id, TaskState.FAILED, 81, TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO, draft,
                                  TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO)
            return
        await save_task_state(task_id, TaskState.PROCESSING, 95,
                              TaskDetailState.GENERATING_FINAL_VIDEO, draft, task_progress.dict())
        task_progress.final_videos = final_video_path
        await save_task_state(task_id, TaskState.COMPLETE, 100, TaskDetailState.FINAL_VIDEO_GENERATION_COMPLETE, draft,
                              task_progress.dict())

        # 更新草稿
        draft.update_duration(task_progress.audio_duration)
        draft.save_to_file(utils.task_dir(task_id))

        logger.success(f"task {task_id} finished, generated final video: {final_video_path}.")
    except ValueError as e:
        await handle_task_failure(task_id, TaskFailureReason.VALUE_ERROR, str(e), task_progress, draft)
        await save_task_state(task_id, TaskState.FAILED, 100, TaskDetailState.FAILED, draft,
                              TaskFailureReason.VALUE_ERROR)
    except Exception as e:
        await handle_task_failure(task_id, TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO, str(e), task_progress,
                                  draft)
        await save_task_state(task_id, TaskState.FAILED, 100, TaskDetailState.FAILED, draft,
                              TaskFailureReason.FAILED_GENERATING_FINAL_VIDEO)

    end_time = time.time()
    minutes, seconds = calculate_duration(start_time, end_time)
    logger.info(f"生成时长为：{minutes} 分钟 {seconds} 秒")
    return task_progress.dict()


async def combine_videos(task_id, params, downloaded_videos, audio_file, images_files, task_progress,
                         draft):
    combined_video_path = []
    video_concat_mode = params.video_concat_mode
    if params.video_count > 1:
        video_concat_mode = VideoConcatMode.random

    _progress = 79
    progress_increment = 10 / params.video_count  # Adjusting progress increment for 80 to 90 range
    start_time = 0

    for i in range(params.video_count):
        index = i + 1
        combined_video = path.join(utils.task_dir(task_id), f"combined-{index}.mp4")
        logger.info(f"\n\n## combining video: {index} => {combined_video}")
        video_generator.combine_videos(
            combined_video_path=combined_video,
            video_paths=downloaded_videos,
            audio_file=audio_file,
            video_aspect=params.video_aspect, video_concat_mode=video_concat_mode,
            max_clip_duration=params.video_clip_duration, images_files=images_files,
            threads=params.n_threads)

        _progress += progress_increment
        task_progress.combined_videos.append(combined_video)
        await save_task_state(task_id, TaskState.PROCESSING, _progress, TaskDetailState.COMBINING_VIDEOS, draft,
                              task_progress.dict())

        combined_video_path.append(combined_video)

        # 更新草稿
        duration = video_generator.get_duration(combined_video)

        start_time += duration

    draft.save_to_file(utils.task_dir(task_id))

    return combined_video_path


async def generate_final_video(task_id, video_title, params, combined_video_path, images_files,audio_file, bgm_file, subtitle_path,
                               task_progress,
                               draft):
    final_video_paths = []
    _progress = 90

    for i, combined_video in enumerate(combined_video_path):
        final_video = path.join(utils.task_dir(task_id), f"final-{i + 1}.mp4")
        logger.info(f"\n\n## generating final video: {i + 1} => {final_video}")

        video_generator.generate_video(task_id=task_id, title=video_title, video_path=combined_video,images_path=images_files,
                                       audio_path=audio_file,
                                       bgm_path=bgm_file,
                                       subtitle_path=subtitle_path, output_file=final_video, params=params)
        _progress += 1
        await save_task_state(task_id, TaskState.PROCESSING, _progress, TaskDetailState.GENERATING_FINAL_VIDEO, draft)
        _progress += 50 / len(combined_video_path) / 2
        task_progress.final_videos.append(final_video)
        final_video_paths.append(final_video)
    return final_video_paths


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


async def handle_task_failure(task_id, failure_reason, error, task_progress, draft):
    logger.error(f"task failed: {task_id} cause by {traceback.format_exc()}")
    if redis_instance is not None:
        await redis_instance.update_task(task_id, state=TaskState.FAILED, progress=100, failure_reason=failure_reason,
                                         error=error, **task_progress.dict())
    else:
        logger.warning(f"redis_service is None, unable to update task {task_id} state to failed")
    # 保存草稿
    draft.save_to_file(utils.task_dir(task_id))


async def save_task_state(task_id, state, progress, detail_state, draft, extra=None):
    task = await task_controller.get_by_task_id(task_id)
    if task:
        task_update = TaskUpdate(
            id=task.id,
            user_id=task.user_id,
            task_id=task_id,
            progress=progress,
            state=state,
            draft_content=draft.to_dict(),
            detail_state=detail_state,
        )
        await task_controller.update(obj_in=task_update)

    # 保存到 Redis
    data = {"state": state, "progress": progress, "detail_state": detail_state}
    if redis_instance is not None:
        await redis_instance.update_task(task_id, **data)
    else:
        logger.warning(f"redis_service is None, unable to update task {task_id} state")


def restore_task_progress_from_draft(draft: Draft) -> TaskProgress:
    task_progress = TaskProgress()
    script_info = draft.draft["script_info"]
    task_progress.script = script_info["video_script"]
    task_progress.video_title = script_info["video_title"]
    task_progress.search_terms = script_info["video_terms"]

    materials = draft.draft["materials"]
    task_progress.audio_file = materials["audios"][0]["path"] if materials["audios"] else None
    task_progress.audio_duration = materials["audios"][0]["duration"] if materials["audios"] else 0
    task_progress.subtitle_file = materials["subtitles"][0]["path"] if materials["subtitles"] else None
    task_progress.images_files = [img["path"] for img in materials["images"]] if materials["images"] else []
    task_progress.downloaded_videos = [video["path"] for video in materials["videos"]] if materials["videos"] else []

    return task_progress
