import asyncio
from pathlib import Path
import json

from conf import BASE_DIR
from douyin_uploader.main import douyin_setup, DouYinVideo
from utils.files_times import generate_schedule_time_next_day


# 读取draft.json文件并获取video_title
def get_video_title(draft_path):
    with open(draft_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data.get('script_info', {}).get('video_title', 'No Title')


if __name__ == '__main__':
    # 设置基础目录和账号文件路径
    base_dir = Path(BASE_DIR)
    account_file = base_dir / "douyin_uploader" / "account.json"

    # 获取视频任务目录
    tasks_dir = base_dir / "tasks"

    # 获取所有video-开头的文件夹
    video_folders = [folder for folder in tasks_dir.glob("video-*") if folder.is_dir()]
    file_num = len(video_folders)

    # 生成发布时间
    publish_datetimes = 0
    # 设置cookie
    cookie_setup = asyncio.run(douyin_setup(account_file, handle=False))

    for index, folder in enumerate(video_folders):
        draft_path = folder / "draft.json"
        video_file = folder / "final-1.mp4"

        if draft_path.exists() and video_file.exists():
            # 获取视频标题
            title = get_video_title(draft_path)
            tags = ['热门', '中视频伙伴计划']

            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{video_file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")

            # 创建并上传视频
            app = DouYinVideo(title, video_file, tags, publish_datetimes, account_file)
            asyncio.run(app.main(), debug=True)
