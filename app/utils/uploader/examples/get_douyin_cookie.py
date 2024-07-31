import asyncio
from pathlib import Path

from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.douyin_uploader.main import douyin_setup


def get_douoyin_cookies():
    account_file = Path(BASE_DIR / "douyin_uploader" / "account.json")
    cookie_setup = asyncio.run(douyin_setup(str(account_file), handle=True))
if __name__ == '__main__':
    get_douoyin_cookies()

