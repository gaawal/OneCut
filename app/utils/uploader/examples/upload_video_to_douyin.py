import asyncio
import os.path
import random
from pathlib import Path
import json

from loguru import logger

from app.utils import utils
from app.utils.uploader.conf import BASE_DIR
from app.utils.uploader.douyin_uploader.main import douyin_setup, DouYinVideo


# 读取draft.json文件并获取video_title和script
def get_video_title_and_script(draft_path):
    with open(draft_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        title = data.get('script_info', {}).get('video_title', '标题')
        script = data.get('script_info', {}).get('script', '内容')
        video_tags = data.get('script_info', {}).get('video_tags', '热门')
        return title, script, video_tags


# 自动发布抖音视频
async def auto_upload_douyin(account_list,task_id):
    logger.info(f"自动发布至抖音，任务id：{task_id}")
    base_dir = Path(BASE_DIR)

    account = random.choice(account_list)
    logger.info(f"随机选取上传账号为{account}")
    account_file = os.path.join(base_dir, "douyin_uploader", account)

    # 获取视频任务目录
    tasks_dir = utils.task_dir()
    task_folder = os.path.join(tasks_dir, task_id)

    if not os.path.exists(task_folder):
        logger.warning(f"任务目录 {task_folder} 不存在")
        return

    draft_path = os.path.join(task_folder, "draft.json")
    video_file = os.path.join(task_folder, "final-1.mp4")

    try:
        if os.path.exists(draft_path) and os.path.exists(video_file):
            # 获取视频标题和脚本
            title, script, tags = get_video_title_and_script(draft_path)
            # 打印视频文件名、标题和 hashtag
            logger.info(f"视频文件名：{video_file}")
            logger.info(f"标题：{title}, 脚本：{script}")
            logger.info(f"视频话题：{tags}")

            # 设置cookie
            await douyin_setup(account_file, handle=False)

            # 创建并上传视频
            app = DouYinVideo(title, video_file, tags, 0, account_file)
            return await app.main()
        else:
            raise Exception(f"draft.json 或 final-1.mp4 在目录 {task_folder} 中不存在")

    except Exception as e:
        logger.warning(f"[Douyin] 上传视频失败 {str(e)}")
        return False

