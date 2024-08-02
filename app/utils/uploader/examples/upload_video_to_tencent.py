import asyncio
import os
import random
from pathlib import Path

from loguru import logger

from app.utils import utils
from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.examples.upload_video_to_douyin import get_video_title_and_script
from app.utils.uploader.tencent_uploader.main import weixin_setup, TencentVideo
from app.utils.uploader.utils.constant import TencentZoneTypes
from app.utils.uploader.utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags


async def auto_upload_weixin(task_id):
    logger.info(f"自动发布至视频号，任务id：{task_id}")
    base_dir = Path(BASE_DIR)
    account_list = ["account.json"]
    account = random.choice(account_list)
    logger.info(f"随机选取上传账号为{account}")
    account_file = os.path.join(base_dir, "tencent_uploader", account)

    # 获取视频任务目录
    tasks_dir = utils.task_dir()
    task_folder = os.path.join(tasks_dir, task_id)

    if not os.path.exists(task_folder):
        logger.warning(f"任务目录 {task_folder} 不存在")
        return

    draft_path = os.path.join(task_folder, "draft.json")
    video_file = os.path.join(task_folder, "final-1.mp4")

    if os.path.exists(draft_path) and os.path.exists(video_file):
        # 获取视频标题和脚本
        title, script, tags = get_video_title_and_script(draft_path)
        # 打印视频文件名、标题和 hashtag
        logger.info(f"视频文件名：{video_file}")
        logger.info(f"标题：{title}, 脚本：{script}")
        logger.info(f"视频话题：{tags}")
        cookie_setup = await weixin_setup(account_file, handle=True)
        category = TencentZoneTypes.LIFESTYLE.value  # 标记原创需要否则不需要传
        # 创建并上传视频
        app = TencentVideo(title, video_file, tags, 0, account_file, category)
        await app.main()
        return True
    return False


if __name__ == '__main__':
    filepath = Path(BASE_DIR) / "videos"
    account_file = Path(BASE_DIR / "tencent_uploader" / "account.json")
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[16])
    cookie_setup = asyncio.run(weixin_setup(account_file, handle=True))
    category = TencentZoneTypes.LIFESTYLE.value  # 标记原创需要否则不需要传
    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        # 打印视频文件名、标题和 hashtag
        print(f"视频文件名：{file}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        app = TencentVideo(title, file, tags, publish_datetimes[index], account_file, category)
        asyncio.run(app.main(), debug=False)
