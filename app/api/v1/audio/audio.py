import glob
import json

import os
import traceback

import requests
from fastapi import Request, UploadFile, APIRouter, Depends, HTTPException
from fastapi.params import File
from fastapi.responses import FileResponse
from loguru import logger
from mutagen.mp3 import MP3

from app.manager.memory_manager import InMemoryTaskManager
from app.manager.redis_manager import RedisTaskManager
from app.models.exception import HttpException
from app.schemas import Success, Fail
from app.schemas.movies import BgmUploadResponse, BgmRetrieveResponse, VoiceRetrieveResponse, StreamAudioRequest
from app.schemas.voice_tts import TTSRequest
from app.services import voice
from app.services.redis_service import RedisService
from app.services.voice import get_all_azure_voices
from app.settings import movies_config
from app.utils import request_base
from app.utils import utils
from app.utils.audio import get_album_art, format_duration, get_audio_metadata, get_waveform_data

router = APIRouter()

_enable_redis = movies_config.app.get("enable_redis", False)
# 根据配置选择合适的任务管理器
if _enable_redis:
    task_manager = RedisTaskManager()
else:
    task_manager = InMemoryTaskManager()
REDIS_WAVEFORM_KEY = "audio_waveform_{}"


@router.get("/voices", response_model=VoiceRetrieveResponse, summary="检索本地朗读清单文件")
def get_voices_list(request: Request):
    voices = get_all_azure_voices()
    response = {
        "voices": voices
    }
    return Success(data=response)


@router.get("/bgms", response_model=BgmRetrieveResponse, summary="检索本地BGM文件")
async def get_bgm_list(request: Request):
    redis_service = RedisService(request.app.state.redis)
    cache_key = "bgm_list_cache"
    bgm_file_key = 'bgm_file_cache:{}'
    cached_data = await redis_service.get(cache_key)
    if cached_data:
        response = json.loads(cached_data)
    else:
        song_dir = utils.song_dir()
        genres = os.listdir(song_dir)  # 获取所有风格目录
        bgm_list = []
        for genre in genres:
            genre_dir = os.path.join(song_dir, genre)
            if os.path.isdir(genre_dir):
                files = glob.glob(os.path.join(genre_dir, "*.mp3"))
                for file in files:
                    audio = MP3(file)
                    image_data, mime_type = await get_album_art(file)
                    audio_metadata = await get_audio_metadata(file)
                    title, artist = audio_metadata
                    name = os.path.basename(file)
                    bgm_info = {
                        "name": name,
                        "title": title if title else name,
                        "artist": artist if artist else '未知',
                        "size": round(os.path.getsize(file) / (1024 * 1024), 2),
                        "duration": await format_duration(int(audio.info.length)),
                        "genres": genre,
                        "image": image_data if image_data else None,
                        "waveform": await get_waveform_data(redis_service, file)  # 获取波形数据
                    }
                    bgm_list.append(bgm_info)
                    await redis_service.set(bgm_file_key.format(name), json.dumps(bgm_info, ensure_ascii=False))
                    logger.info(f"save bgm file index {name} success")
        bgm_list_sorted = sorted(bgm_list, key=lambda x: x["name"])
        response = {"files": bgm_list_sorted}
        await redis_service.set(cache_key, json.dumps(response, ensure_ascii=False))

    return Success(data=response)


@router.get("/stream-audio/{file_path:path}", summary="流媒体播放音频文件")
async def stream_audio(request: Request, file_path: str, params: StreamAudioRequest = Depends()):
    song_dir = utils.song_dir()
    genre = params.genre
    file_path = os.path.join(song_dir, genre, file_path)  # 获取路径
    try:
        return FileResponse(file_path, media_type="audio/mpeg")
    except FileNotFoundError:
        return Fail(msg="获取不到文件信息！", code=404)


@router.get("/stream-voice/{file_path:path}", summary="流媒体播放人声文件")
async def stream_voice(request: Request, file_path: str):
    try:
        suffix = ".mp3"
        voice_dir = utils.voice_dir()
        parts = file_path.split('-')
        if len(parts) < 3:
            raise ValueError("Invalid name format")
        language = parts[0]
        play_content = utils.tr("Voice Example", language)
        audio_file = os.path.join(voice_dir, f'{file_path}{suffix}')  # 获取路径
        logger.info(f"stream_voice audio_file is {audio_file}")
        # 如果文件存在，直接返回
        if os.path.exists(audio_file):
            logger.success(f"stream voice audio_file is exists，return {audio_file}")
            return FileResponse(audio_file, media_type="audio/mpeg")
        # 如果文件不存在，进行生成
        voice_name = file_path
        # 生成音频文件
        sub_maker = await voice.tts(play_content, voice_name, audio_file)
        if sub_maker and os.path.exists(audio_file):
            return FileResponse(audio_file, media_type="audio/mpeg")
        else:
            return Fail(error="获取不到文件信息", code=404)
    except FileNotFoundError:
        logger.error(traceback.format_exc())
        return Fail(error="获取不到文件信息", code=404)
    except Exception as e:
        logger.error(traceback.format_exc())
        return Fail(error=str(e), code=500)


@router.post("/uploadBgm", response_model=BgmUploadResponse, summary="将BGM文件上传到歌曲目录")
def upload_bgm_file(request: Request, file: UploadFile = File(...)):
    request_id = request_base.get_task_id(request)
    # check file ext
    if file.filename.endswith('mp3'):
        song_dir = utils.song_dir()
        save_path = os.path.join(song_dir, file.filename)
        # save file
        with open(save_path, "wb+") as buffer:
            # If the file already exists, it will be overwritten
            file.file.seek(0)
            buffer.write(file.file.read())
        response = {
            "file": save_path
        }
        return Success(data=response)

    raise HttpException('', status_code=400, message=f"{request_id}: Only *.mp3 files can be uploaded")


@router.post("/chat_tts")
def generate_tts(request: TTSRequest):
    try:
        chat_tts_url = movies_config.app.get("chat_tts_url", "")
        response = requests.post(chat_tts_url, data=request.dict())
        response_data = response.json()

        if response_data.get("code") == 0:
            return response_data["audio_files"]
        else:
            raise HTTPException(status_code=400, detail=response_data.get("msg", "Error occurred"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
