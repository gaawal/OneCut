# -- coding: utf-8 --
# @Time : 2024/5/27 10:52
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : llm_generator.py

from enum import Enum
from typing import Any, Optional, List, Dict

import pydantic
from pydantic import BaseModel
import warnings

# 忽略 Pydantic 的特定警告
from app.utils.utils import load_locales, i18n_dir

warnings.filterwarnings("ignore", category=UserWarning, message="Field name.*shadows an attribute in parent.*")


class VideoConcatMode(str, Enum):
    random = "random"
    sequential = "sequential"


class VideoAspect(str, Enum):
    landscape = "16:9"
    portrait = "9:16"
    square = "1:1"

    def to_resolution(self):
        if self == VideoAspect.landscape.value:
            return 1920, 1080
        elif self == VideoAspect.portrait.value:
            return 1080, 1920
        elif self == VideoAspect.square.value:
            return 1080, 1080
        return 1080, 1920


class _Config:
    arbitrary_types_allowed = True


@pydantic.dataclasses.dataclass(config=_Config)
class MaterialInfo:
    provider: str = "pexels"
    url: str = ""
    duration: int = 0


class PlayAudioParams(BaseModel):
    genre: str = ''  # 音频的风格文件夹


class VideoParams(BaseModel):
    video_subject: str  # 视频主题
    video_script: str = ""  # 用于生成视频的脚本
    video_tags: list = []  # 用于发布视频的话题
    word_count: int = 300  # 文案字数
    video_category: str = "auto-detect"  # 用于生成视频文案的风格
    video_terms: Optional[str | list] = None  # 用于生成视频的关键词
    video_aspect: Optional[VideoAspect] = VideoAspect.portrait.value
    video_concat_mode: Optional[VideoConcatMode] = VideoConcatMode.random.value
    video_clip_duration: Optional[int] = 5
    video_count: Optional[int] = 1

    video_source: Optional[str] = "pexels"
    video_materials: Optional[List[MaterialInfo]] = None  # 用于生成视频的素材

    video_language: Optional[str] = ""  # auto detect

    voice_name: Optional[str] = ""
    voice_volume: Optional[float] = 1.0
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2

    subtitle_enabled: Optional[bool] = True
    subtitle_position: Optional[str] = "bottom"  # top, bottom, center
    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Optional[str] = "transparent"
    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5
    font_opacity: float = 1

    paragraph_number: Optional[int] = 1
    amount: Optional[int] = 5
    fps: Optional[int] = 30
    video_durations: List[int] = []
    weibo_mid: Optional[str] = ""
    weibo_title: Optional[str] = ""
    auto_generate: Optional[bool] = False


class VideoScriptParams:
    """
    {
      "video_subject": "春天的花海",
      "video_language": "",
      "paragraph_number": 1
    }
    """
    video_subject: Optional[str] = "春天的花海"
    origin_script: Optional[str] = ""
    video_language: Optional[str] = ""
    paragraph_number: Optional[int] = 1
    video_category: Optional[str] = "auto-detect"
    word_count: Optional[int] = 300
    amount: Optional[int] = 5
    weibo_mid: Optional[str] = ""
    weibo_url: Optional[str] = ""
    weibo_title: Optional[str] = ""
    video_inspire: Optional[str] = ""
    video_inspire_keyword: Optional[str] = ""


class VideoTermsParams:
    """
    {
      "video_subject": "",
      "video_script": "",
      "amount": 5
    }
    """
    video_subject: Optional[str] = "春天的花海"
    video_script: Optional[str] = "春天的花海，如诗如画般展现在眼前。万物复苏的季节里，大地披上了一袭绚丽多彩的盛装。金黄的迎春、粉嫩的樱花、洁白的梨花、艳丽的郁金香……"
    amount: Optional[int] = 5


class TaskProgress(BaseModel):
    """
    视频生成任务的参数
    """
    script: Optional[str] = None
    video_title: Optional[str] = None
    search_terms: Optional[List[str]] = None
    video_tags: Optional[List[str]] = None
    audio_file: Optional[str] = None
    bgm_file: Optional[str] = None
    images_files: Optional[List[str]] = None
    audio_duration: Optional[int] = 0
    subtitle_file: Optional[str] = None
    downloaded_videos: Optional[List[str]] = None
    combined_videos: Optional[List[str]] = []
    final_videos: Optional[List[str]] = []
    other_details: Optional[Dict[str, Any]] = None
    total_duration: Optional[float] = 0


class BaseResponse(BaseModel):
    status: int = 200
    message: Optional[str] = 'success'
    data: Any = None


class TaskVideoRequest(VideoParams, BaseModel):
    pass


class StreamAudioRequest(PlayAudioParams, BaseModel):
    pass


class TaskQueryRequest(BaseModel):
    pass


class VideoScriptRequest(VideoScriptParams, BaseModel):
    pass


class VideoTermsRequest(VideoTermsParams, BaseModel):
    pass


class TaskResponse(BaseResponse):
    class TaskResponseData(BaseModel):
        task_id: str

    data: TaskResponseData

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "task_id": "6c85c8cc-a77a-42b9-bc30-947815aa0558"
                }
            },
        }


class TaskQueryResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "state": 1,
                    "progress": 100,
                    "videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/final-1.mp4"
                    ],
                    "combined_videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/combined-1.mp4"
                    ]
                }
            },
        }


class ThumbnailRequest(BaseModel):
    video_ids: List[str]


class TaskDeletionResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "state": 1,
                    "progress": 100,
                    "videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/final-1.mp4"
                    ],
                    "combined_videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/combined-1.mp4"
                    ]
                }
            },
        }


class VideoScriptResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "video_script": "春天的花海，是大自然的一幅美丽画卷。在这个季节里，大地复苏，万物生长，花朵争相绽放，形成了一片五彩斑斓的花海..."
                }
            },
        }


class VideoTermsResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "video_terms": ["sky", "tree"]
                }
            },
        }


class Voice(BaseModel):
    name: str
    gender: str
    language: str
    country: str
    voice: str

    @classmethod
    def from_name(cls, name: str, gender: str):
        parts = name.split('-')
        if len(parts) < 3:
            raise ValueError("Invalid name format")
        language = parts[0]
        locales = load_locales(i18n_dir())
        country = parts[1]
        voice = "-".join(parts[2:])
        return cls(name=name, gender=gender, language=language, country=country, voice=voice)


class VoiceRetrieveResponse(BaseResponse):
    files: List[Voice]

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "files": [
                        {
                            "name": "demo",
                            "gender": "demo",
                            "language": "demo",
                            "country": "demo",
                            "voice": "demo",
                        },
                    ]
                }
            },
        }


class BgmFile(BaseModel):
    name: str
    title: str
    artist: str
    duration: str
    genres: str
    file: str
    image: str = None
    mime_type: str


class BgmRetrieveResponse(BaseResponse):
    files: List[BgmFile]

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "files": [
                        {
                            "name": "demo.mp3",
                            "title": "demo",
                            "artist": "EVO MUSIC",
                            "size": 7.75,
                            "duration": "03:21",
                            "genres": "happy",
                            "file": "http://127.0.0.1:9999/api/v1/audio/stream-audio/demo.mp3",
                            "image": "base64code",
                            "mime_type": "image/jpg"
                        },
                    ]
                }
            },
        }


class BgmUploadResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "file": "/MoneyPrinterTurbo/resource/songs/example.mp3"
                }
            },
        }

class TaskListRequest(BaseModel):
    page: int
    page_size: int
    query: Optional[str] = None
    sort: Optional[str] = None
    publishStatus: Optional[str] = None
    taskStatus: Optional[str] = None


class TaskIdRequest(BaseModel):
    task_id: str


class TaskCreateRequest(BaseModel):
    user_id: int
    task_id: str
    progress: int
    state: str
    draft_content: dict


class TaskUpdateRequest(BaseModel):
    id: int
    progress: int
    state: str
    draft_content: dict


class WeiboArticle(BaseModel):
    nickname: Optional[str] = None
    comment: Optional[str] = None
    screenshot_path: str = ""
    images: List[str]


class WeiboArticleData(BaseModel):
    weibo_mid: Optional[str] = ""
    url: Optional[str] = ""
    introduction: Optional[str] = ""
    articles: List[WeiboArticle] = []
    is_generated: Optional[bool] = False # 是否自动生成视频了


class HotSearchItem(BaseModel):
    mid: str
    category: Optional[str] = None
    title: str
    hot: Optional[int] = None
    url: str
    collect_status: Optional[int] = 0
