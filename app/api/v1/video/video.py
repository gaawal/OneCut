import os
import pathlib
import shutil

from fastapi import Request, Depends, Path, BackgroundTasks, APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from moviepy.video.io.VideoFileClip import VideoFileClip

from app.constant.redis_const import RedisKeyPrefix
from app.manager.redis_manager import redis_taskmanager
from app.models.exception import HttpException
from app.schemas import Success, Fail
from app.schemas.movies import TaskVideoRequest, TaskQueryResponse, TaskResponse, TaskQueryRequest, \
    TaskDeletionResponse, ThumbnailRequest
from app.services import video_controller as generate_video_task, video_controller
from app.services.redis_service import redis_instance
from app.settings import movies_config
from app.utils import request_base
from app.utils import utils
from app.utils.utils import tr

router = APIRouter()


@router.post("/createVideos", response_model=TaskResponse, summary="生成短视频")
async def create_video(request: Request, params: TaskVideoRequest):
    task_id = RedisKeyPrefix.VIDEO_TASK.format(utils.get_uuid())
    request_id = request_base.get_task_id(request)
    task = {
        "task_id": task_id,
        "request_id": request_id,
        "params": params.dict(),
    }
    try:
        if not params.video_subject and not params.video_script:
            raise ValueError(tr("Video Script and Subject Cannot Both Be Empty"))
        if params.video_source not in ["pexels", "pixabay", "local"]:
            raise ValueError(tr("Please Select a Valid Video Source"))
        if params.video_source == "pexels" and not movies_config.app.get("pexels_api_keys", ""):
            raise ValueError(tr("Please Enter the Pexels API Key"))
        if params.video_source == "Pixabay" and not movies_config.app.get("pixabay_api_keys", ""):
            raise ValueError(tr("Please Enter the Pixabay API Key"))
        if not params.voice_name:
            raise ValueError(tr("Please select a Valid Voice Source"))

        await redis_instance.update_task(task_id)
        await redis_taskmanager.add_task(video_controller.start, task_id=task_id, params=params)
        logger.info(f"视频生成任务已创建: {utils.to_json(task)}\ntask_id is {task_id} ")

        return Success(data=task)
    except ValueError as e:
        return Fail(data=task, code=400, msg=f"{str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskQueryResponse, summary="查询任务状态")
async def get_task(request: Request, task_id: str = Path(..., description="Task ID"),
                   query: TaskQueryRequest = Depends()):
    endpoint = movies_config.app.get("endpoint", "")
    if not endpoint:
        endpoint = str(request.base_url)
    endpoint = endpoint.rstrip("/")

    request_id = request_base.get_task_id(request)
    task = await redis_instance.get_task(task_id)
    if task:
        task_dir = utils.task_dir()

        def file_to_uri(file):
            if not file.startswith(endpoint):
                _uri_path = v.replace(task_dir, "tasks").replace("\\", "/")
                _uri_path = f"{endpoint}/{_uri_path}"
            else:
                _uri_path = file
            return _uri_path

        if "videos" in task:
            videos = task["videos"]
            urls = []
            for v in videos:
                urls.append(file_to_uri(v))
            task["videos"] = urls
        if "combined_videos" in task:
            combined_videos = task["combined_videos"]
            urls = []
            for v in combined_videos:
                urls.append(file_to_uri(v))
            task["combined_videos"] = urls
        return Success(data=task)

    raise HttpException(task_id=task_id, status_code=404, message=f"{request_id}: task not found")


# 获取或生成缩略图
@router.post("/thumbnails/", summary="查询任务状态")
async def get_thumbnails(request: Request, params: ThumbnailRequest):
    thumbnail_urls = []
    cache_dir = utils.storage_dir("cache_videos")
    for video_id in params.video_ids:
        video_path = os.path.join(cache_dir, video_id)
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file {video_id} not found in task {request.task_id}")

        output_thumbnail_path = f"thumbnails/{request.task_id}_{video_id}.png"

        # 如果缩略图不存在，则生成缩略图
        if not os.path.exists(output_thumbnail_path):
            with VideoFileClip(video_path) as video:
                frame = video.get_frame(1)  # 获取第1秒的帧
                video.save_frame(output_thumbnail_path, t=1)

        thumbnail_url = f"/thumbnails/{request.task_id}_{video_id}.png"
        thumbnail_urls.append(thumbnail_url)

    return Success(data={"thumbnails": thumbnail_urls})


@router.delete("/tasks/{task_id}", response_model=TaskDeletionResponse, summary="删除生成的短视频任务")
async def delete_video(request: Request, task_id: str = Path(..., description="Task ID")):
    request_id = request_base.get_task_id(request)
    task = redis_instance.get_task(task_id)
    if task:
        tasks_dir = utils.task_dir()
        current_task_dir = os.path.join(tasks_dir, task_id)
        if os.path.exists(current_task_dir):
            shutil.rmtree(current_task_dir)

        await redis_instance.delete_task(task_id)
        logger.success(f"video deleted: {utils.to_json(task)}")
        return utils.get_response(200)

    raise HttpException(task_id=task_id, status_code=404, message=f"{request_id}: task not found")


@router.get("/stream/{file_path:path}", summary="视频流媒体播放视频文件")
async def stream_video(request: Request, file_path: str):
    tasks_dir = utils.task_dir()
    video_path = os.path.join(tasks_dir, file_path)
    range_header = request.headers.get('Range')
    video_size = os.path.getsize(video_path)
    start, end = 0, video_size - 1

    length = video_size
    if range_header:
        range_ = range_header.split('bytes=')[1]
        start, end = [int(part) if part else None for part in range_.split('-')]
        if start is None:
            start = video_size - end
            end = video_size - 1
        if end is None:
            end = video_size - 1
        length = end - start + 1

    def file_iterator(file_path, offset=0, bytes_to_read=None):
        with open(file_path, 'rb') as f:
            f.seek(offset, os.SEEK_SET)
            remaining = bytes_to_read or video_size
            while remaining > 0:
                bytes_to_read = min(4096, remaining)
                data = f.read(bytes_to_read)
                if not data:
                    break
                remaining -= len(data)
                yield data

    response = StreamingResponse(file_iterator(video_path, start, length), media_type='video/mp4')
    response.headers['Content-Range'] = f'bytes {start}-{end}/{video_size}'
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Length'] = str(length)
    response.status_code = 206  # Partial Content

    return response


@router.get("/download/{file_path:path}", summary="下载最终生成的视频文件")
async def download_video(_: Request, file_path: str):
    """
    download video
    :param _: Request request
    :param file_path: video file path, eg: /cd1727ed-3473-42a2-a7da-4faafafec72b/final-1.mp4
    :return: video file
    """
    tasks_dir = utils.task_dir()
    video_path = os.path.join(tasks_dir, file_path)
    file_path = pathlib.Path(video_path)
    filename = file_path.stem
    extension = file_path.suffix
    headers = {
        "Content-Disposition": f"attachment; filename={filename}{extension}"
    }
    return FileResponse(path=video_path, headers=headers, filename=f"{filename}{extension}",
                        media_type=f'video/{extension[1:]}')


@router.get("/stream_video", summary="返回生成的视频文件")
async def stream_video(task_id: str = Query(...)):
    # 假设视频文件保存在一个以 task_id 命名的目录下
    video_dir = os.path.join(utils.task_dir(), task_id)
    video_path = os.path.join(video_dir, "final-1.mp4")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件未找到")

    # 返回视频文件
    return FileResponse(video_path, media_type="video/mpeg")

