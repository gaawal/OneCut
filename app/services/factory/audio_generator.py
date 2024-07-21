# -- coding: utf-8 --
# @Time : 2024/7/21 08:26
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : audio_generator.py
# @Software: PyCharm
import json
import os
import random

from loguru import logger

from app.services import redis_service
from app.utils import utils


async def get_bgm_file(request, bgm_type="random", bgm_file=""):
    logger.info(f"get bgm file, bgm_type is {bgm_type}, bgm_file is {bgm_file}")
    suffix = ".mp3"
    choose_bgm_file = ""
    song_dir = utils.song_dir()

    if not bgm_file and bgm_type == "random":
        cache_key = "bgm_list_cache"
        cached_data = await redis_service.get(cache_key)
        if cached_data:
            logger.success("get bgm list in redis cache ok, try to random choice it")
            response = json.loads(cached_data)
            files = response.get("files")
            random_file_info = random.choice(files)
            genres = random_file_info.get("genres")
            name = random_file_info.get("name")
            choose_bgm_file = os.path.join(song_dir, genres, name)
            logger.info(f"random choice bgm file is {choose_bgm_file}")
    else:
        bgm_file_key = "bgm_file_cache:"
        cache_bgm_key = f"{bgm_file_key}{bgm_file}{suffix}"
        if not bgm_type:
            logger.warning(f"get bgm file failed, {bgm_file} is not available")
            return ""
        cached_data = await redis_service.get(cache_bgm_key)
        if cached_data:
            logger.success(f"get bgm in redis cache ok, redis key is {cache_bgm_key}")
            bgm_info = json.loads(cached_data)
            genres = bgm_info.get("genres")
            name = bgm_info.get("name")
            choose_bgm_file = os.path.join(song_dir, genres, name)
        else:
            logger.warning(f"No bgm in redis cache, redis key is {cache_bgm_key}")
    if not choose_bgm_file or not os.path.exists(choose_bgm_file):
        logger.info(f"No bgm file found at path {choose_bgm_file}")

    return choose_bgm_file