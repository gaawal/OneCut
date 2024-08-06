import asyncio
import os
from pathlib import Path

from loguru import logger

from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.xigua_uploader.main import xigua_setup


def get_xigua_cookies(account_list):
    base_dir = Path(BASE_DIR)
    for account in account_list:
        logger.info(f"检测选取账号为{account}")
        account_file = os.path.join(base_dir, "xigua_uploader", account)
        cookie_setup = asyncio.run(xigua_setup(str(account_file), handle=True))


if __name__ == '__main__':
    account_file = Path(BASE_DIR / "xigua_uploader" / "account.json")
    cookie_setup = asyncio.run(xigua_setup(str(account_file), handle=True))
