import asyncio
import os
from pathlib import Path

from app.utils.crawler.weibo_crawler.main import weibo_setup


async def get_weibo_cookies():
    BASE_DIR = Path(__file__).parent.resolve()
    base_dir = Path(BASE_DIR)
    cookie_file = 'WeiboCookie.json'
    cookie_file = os.path.join(base_dir, cookie_file)
    return await weibo_setup(str(cookie_file), handle=True)


if __name__ == '__main__':
    asyncio.run(get_weibo_cookies())
