import asyncio
import os
import random
from pathlib import Path

from loguru import logger

from app.services.hotspot.main import weibo_setup
from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.douyin_uploader.main import douyin_setup


async def get_weibo_cookies():
    base_dir = Path(BASE_DIR)
    cookie_file = 'WeiboCookie.json'
    cookie_file = os.path.join(base_dir, "weibo_uploader", cookie_file)
    return await weibo_setup(str(cookie_file), handle=True)


if __name__ == '__main__':
    get_weibo_cookies()
