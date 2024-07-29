import asyncio
from pathlib import Path

from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.tencent_uploader.main import weixin_setup

if __name__ == '__main__':
    account_file = Path(BASE_DIR / "tencent_uploader" / "account.json")
    cookie_setup = asyncio.run(weixin_setup(str(account_file), handle=True))
