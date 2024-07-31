import os
import random
import traceback
import aiohttp
import asyncio
from urllib.parse import urlencode

import requests
from typing import List
from loguru import logger

from app.schemas.drafts import Draft
from app.settings import movies_config
from app.schemas.movies import VideoAspect, VideoConcatMode, MaterialInfo
from app.utils import utils

# 确保 proxy 参数是字符串类型
proxy_config = movies_config.proxy
proxy = proxy_config.get("http") if isinstance(proxy_config, dict) else None

requested_count = 0


async def fetch_video_details(item, video_aspect, max_clip_duration):
    # 模拟调用接口获取视频时长
    video_details = {
        "url": item.url,
        "duration": min(max_clip_duration, item.duration),
        "aspect": video_aspect
    }
    return video_details


async def download_video(item, material_directory, video_paths, draft, draft_dir, start_time):
    try:
        url_without_query = item['url']
        url_hash = utils.md5(url_without_query)
        video_id = f"vid-{url_hash}"
        logger.info(f"downloading video_id is: {video_id}")
        video_path = os.path.join(material_directory, f"{video_id}.mp4")

        # 如果视频已经存在，直接返回路径
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            logger.info(f"video_id {video_id} already exists to use it: {video_path}")
            video_paths.append(video_path)
            draft.add_material("videos", {"path": video_path, "duration": item['duration'], "aspect": item['aspect']})

            draft.save_to_file(draft_dir)
            return item['duration']

        # 确保 proxy 参数是字符串类型
        proxy_config = movies_config.proxy
        proxy = proxy_config.get("http") if isinstance(proxy_config, dict) else None

        # 下载视频
        async with aiohttp.ClientSession() as session:
            async with session.get(item['url'], proxy=proxy, ssl=False, timeout=240) as resp:
                with open(video_path, 'wb') as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)

        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            video_paths.append(video_path)
            draft.add_material("videos", {"path": video_path, "duration": item['duration'], "aspect": item['aspect']})

            draft.save_to_file(draft_dir)
            return item['duration']
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"failed to download video: {item['url']} => {str(e)}")
    return 0


async def download_videos(task_id: str,
                          search_terms: List[str],
                          source: str = "pexels",
                          video_aspect: VideoAspect = VideoAspect.portrait,
                          video_contact_mode: VideoConcatMode = VideoConcatMode.random,
                          audio_duration: float = 0.0,
                          max_clip_duration: int = 5,
                          draft: Draft = None,
                          draft_dir: str = "") -> List[str]:
    search_videos = search_videos_pexels if source == "pexels" else search_videos_pixabay

    valid_video_items: List[MaterialInfo] = []
    found_duration = 0.0

    for search_term in search_terms:
        video_items = search_videos(search_term=search_term, minimum_duration=max_clip_duration,
                                    video_aspect=video_aspect)
        valid_video_items.extend(video_items)
        if found_duration >= audio_duration:
            break

    if video_contact_mode == VideoConcatMode.random:
        random.shuffle(valid_video_items)

    material_directory = movies_config.app.get("material_directory", "").strip()
    if material_directory == "task":
        material_directory = utils.task_dir(task_id)
    else:
        material_directory = utils.cache_videos_dir()

    total_duration = 0.0
    tasks = []
    start_time = 0
    for item in valid_video_items:
        task = fetch_video_details(item, video_aspect, max_clip_duration)
        tasks.append(task)

    video_details = await asyncio.gather(*tasks)

    download_tasks = []
    video_paths = []
    for item in video_details:
        total_duration += item['duration']
        download_tasks.append(download_video(item, material_directory, video_paths, draft, draft_dir, start_time))
        start_time += item['duration']
        if total_duration >= audio_duration:
            break

    await asyncio.gather(*download_tasks)
    logger.success(f"downloaded videos counts is  {len(video_paths)} ")
    return video_paths


def get_api_key(cfg_key: str):
    api_keys = movies_config.app.get(cfg_key)
    if not api_keys:
        raise ValueError(
            f"\n\n##### {cfg_key} is not set #####\n\nPlease set it in the config.toml file: {movies_config.config_file}\n\n"
            f"{utils.to_json(movies_config.app)}")

    # if only one key is provided, return it
    if isinstance(api_keys, str):
        return api_keys

    global requested_count
    requested_count += 1
    return api_keys[requested_count % len(api_keys)]


def search_videos_pexels(search_term: str,
                         minimum_duration: int,
                         video_aspect: VideoAspect = VideoAspect.portrait,
                         ) -> List[MaterialInfo]:
    aspect = VideoAspect(video_aspect)
    video_orientation = aspect.name
    video_width, video_height = aspect.to_resolution()
    api_key = get_api_key("pexels_api_keys")
    headers = {
        "Authorization": api_key
    }
    # Build URL
    params = {
        "query": search_term,
        "per_page": 20,
        "orientation": video_orientation
    }
    query_url = f"https://api.pexels.com/videos/search?{urlencode(params)}"
    logger.info(f"searching videos by search_term: {search_term}")

    try:
        r = requests.get(query_url, headers=headers, proxies=movies_config.proxy, verify=False, timeout=(30, 60))
        response = r.json()
        video_items = []
        if "videos" not in response:
            logger.error(f"search videos failed: {response}")
            return video_items
        videos = response["videos"]
        # loop through each video in the result
        for v in videos:
            duration = v["duration"]
            # check if video has desired minimum duration
            if duration < minimum_duration:
                continue
            video_files = v["video_files"]
            # loop through each url to determine the best quality
            for video in video_files:
                w = int(video["width"])
                h = int(video["height"])
                if w == video_width and h == video_height:
                    item = MaterialInfo()
                    item.provider = "pexels"
                    item.url = video["link"]
                    item.duration = duration
                    video_items.append(item)
                    break
        return video_items
    except Exception as e:
        logger.error(f"search videos failed: {str(e)}")

    return []


def search_videos_pixabay(search_term: str,
                          minimum_duration: int,
                          video_aspect: VideoAspect = VideoAspect.portrait,
                          ) -> List[MaterialInfo]:
    aspect = VideoAspect(video_aspect)

    video_width, video_height = aspect.to_resolution()

    api_key = get_api_key("pixabay_api_keys")
    # Build URL
    query_url = f"https://pixabay.com/api/videos/?q={search_term}&video_type=all&per_page=50&key={api_key}"
    logger.info(f"searching videos by search terms: {search_term} query_url {query_url} ")

    try:
        r = requests.get(query_url, proxies=movies_config.proxy, verify=False, timeout=(30, 60))
        response = r.json()
        video_items = []
        if "hits" not in response:
            logger.error(f"search videos failed: {response}")
            return video_items
        videos = response["hits"]
        # loop through each video in the result
        for v in videos:
            duration = v["duration"]
            # check if video has desired minimum duration
            if duration < minimum_duration:
                continue
            video_files = v["videos"]
            # 循环浏览每个url以确定最佳质量
            for video_type in video_files:
                video = video_files[video_type]
                w = int(video["width"])
                h = int(video["height"])
                if w == video_width and h == video_height:
                    item = MaterialInfo()
                    item.provider = "pixabay"
                    item.url = video["url"]
                    item.thumbnail = video["thumbnail"]
                    item.size = video["size"]
                    item.duration = duration
                    video_items.append(item)
                    break
        return video_items
    except Exception as e:
        logger.error(f"search videos failed: {str(e)}")

    return []


def get_local_videos(audio_duration, video_clip_duration):
    # 计算需要的视频片段总个数乘以2 多取几个
    video_counts = audio_duration // video_clip_duration + 5
    # 获取缓存目录中的视频文件列表
    video_files = [os.path.join(utils.cache_videos_dir(), file) for file in os.listdir(utils.cache_videos_dir()) if
                   file.endswith('.mp4')]
    # 随机选择所需数量的视频文件
    try:
        selected_videos = random.sample(video_files, video_counts)
    except ValueError:
        selected_videos = []
    return selected_videos
