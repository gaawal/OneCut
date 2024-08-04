import asyncio
import os
import random
from pathlib import Path

from loguru import logger

from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.douyin_uploader.main import douyin_setup


def get_douoyin_cookies(account_list):
    base_dir = Path(BASE_DIR)
    for account in account_list:
        logger.info(f"检测选取账号为{account}")
        account_file = os.path.join(base_dir, "douyin_uploader", account)
        cookie_setup = asyncio.run(douyin_setup(str(account_file), handle=True))
if __name__ == '__main__':
    get_douoyin_cookies()

