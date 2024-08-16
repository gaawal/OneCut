import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import aiohttp
from loguru import logger
from moviepy.editor import VideoFileClip

from app.services.factory.video_generator import write_videofile_async
from app.utils import utils


class WeiboCrawler:
    """微博采集器"""
    def __init__(self, video_counts=5, max_video_length=60, save_dir=utils.cache_weibo_videos_dir(), target_types=None,
                 retry_attempts=5, max_open_files=30):
        if target_types is None:
            target_types = ['mp4_720p_mp4', 'mp4_ld_mp4', 'mp4_hd_mp4']
        cookie_file = 'WeiboCookie.json'
        self.target_types = target_types
        self.BASE_DIR = Path(__file__).parent.resolve()
        self.save_dir = self.BASE_DIR / save_dir
        self.cookie_file = self.BASE_DIR / cookie_file
        self.cookies = self.load_cookies(self.cookie_file)
        os.makedirs(self.save_dir, exist_ok=True)
        self.video_counts = video_counts
        self.max_video_length = max_video_length
        self.retry_attempts = retry_attempts
        self.semaphore = asyncio.Semaphore(5)  # 限制同时进行的任务数
        self.file_semaphore = asyncio.Semaphore(max_open_files)  # 限制同时打开的文件数量

    def load_cookies(self, cookie_file):
        """从JSON文件中加载Cookies"""
        with open(cookie_file, 'r') as f:
            cookie_data = json.load(f)
            cookies = {item['name']: item['value'] for item in cookie_data['cookies']}
        return cookies

    async def fetch(self, session, url, params=None):
        """异步获取网页内容"""
        async with session.get(url, params=params, cookies=self.cookies) as response:
            return await response.json()

    async def get_video_url(self, mblog):
        """从mblog中提取视频URL"""
        media_info = {}
        if mblog.get("page_info"):
            if (mblog["page_info"].get("urls") or mblog["page_info"].get("media_info")) and mblog["page_info"].get(
                    "type") == "video":
                media_info = mblog["page_info"]["urls"] or mblog["page_info"]["media_info"]
        return media_info

    async def save_video_segments(self, video_path, segments):
        """根据分割时间点保存视频片段"""
        segment_paths = []

        async with self.file_semaphore:  # 使用信号量限制同时打开的文件数量
            with VideoFileClip(str(video_path)) as video:  # 使用上下文管理器确保资源关闭
                for idx, (start, end) in enumerate(segments):
                    segment_duration = end - start
                    if segment_duration <= self.max_video_length:
                        current_time = datetime.now()
                        formatted_time_str = current_time.strftime("%Y%m%d%H%M")
                        segment_path = self.save_dir / f"{formatted_time_str}-video-segment-{idx + 1}.mp4"
                        segment = video.subclip(start, end)
                        await write_videofile_async(segment, filename=str(segment_path), audio_codec="aac",
                                                    logger=None, fps=30)
                        segment_paths.append(segment_path)
                        logger.info(f"视频片段 {segment_path}，时长 {segment_duration:.2f} 秒")

                    if len(segment_paths) >= self.video_counts:
                        break  # 达到最大视频数量，停止保存

        return segment_paths

    async def collect_videos(self, title, weibo_mid, page_type='searchall'):
        """采集微博视频"""
        async with self.semaphore:  # 控制并发量
            url = 'https://m.weibo.cn/api/container/getIndex'
            params = {
                'containerid': f'100103type=1&t=10&q={title}',
                'stream_entry_id': '152',
                'page_type': page_type,
            }

            async with aiohttp.ClientSession(headers={
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9',
                'mweibo-pwa': '1',
                'referer': 'https://m.weibo.cn/',
                'pragma': 'no-cache',
                'cache-control': 'no-cache',
                'sec-ch-ua': '"Google Chrome";v="127", "Chromium";v="127", "Not)A;Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }) as session:
                weibo_response = await self.fetch(session, url, params)
                weibo_data = weibo_response.get('data')
                if not weibo_data:
                    logger.info("未获取到有效的微博数据")
                    return []

                cards_info = weibo_data.get('cards')
                media_info_list = []
                video_paths = []

                for card in cards_info:
                    card_type = card.get('card_type')
                    if card_type == 9:
                        mblog = card.get('mblog')
                        media_info = await self.get_video_url(mblog)
                        if media_info:
                            media_info_list.append(media_info)

                for idx, item in enumerate(media_info_list):
                    if len(video_paths) >= self.video_counts:
                        break  # 达到最大视频数量，停止下载
                    video_urls = [item.get(target_type) for target_type in self.target_types if item.get(target_type)]
                    if video_urls:
                        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
                        unique_id = uuid.uuid4().hex[:4]
                        filename = f"{current_time}_{unique_id}_{weibo_mid}_weibo_video.mp4"
                        video_path = os.path.join(self.save_dir, filename)
                        await self.save_video_to_local(session, video_urls[0], video_path)
                        # 检查并截取视频片段
                        truncated_path = await self.truncate_video(video_path)
                        video_paths.append(truncated_path)
                    else:
                        logger.info(f"未找到 {self.target_types} 对应的视频 URL")

                return video_paths  # 返回保存的视频文件路径列表

    async def save_video_to_local(self, session, video_url, save_path):
        """异步下载并保存视频到本地，带重试功能"""
        logger.info(f"异步下载并保存视频到本地,{video_url}")
        for attempt in range(self.retry_attempts):
            try:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        with open(save_path, 'wb') as f:  # 使用上下文管理器确保文件关闭
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        logger.info(f"微博视频素材已保存到 {save_path}")
                        return
                    else:
                        logger.info(f"无法下载视频，状态码: {response.status}")
            except aiohttp.ClientError as e:
                logger.warning(f"下载失败，尝试重试 {attempt + 1}/{self.retry_attempts}，错误: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # 指数回退

        logger.error(f"所有重试均失败，未能下载视频 {video_url}")

    async def truncate_video(self, video_path):
        """截取视频至最大长度"""
        try:
            async with self.file_semaphore:  # 使用信号量限制同时打开的文件数量
                with VideoFileClip(str(video_path)) as video:  # 使用上下文管理器确保资源关闭
                    if video.duration > self.max_video_length:
                        logger.info(f"视频长度 {video.duration} 秒，超过最大限制 {self.max_video_length} 秒，截取前 {self.max_video_length} 秒")
                        truncated_path = str(video_path).replace(".mp4", "_truncated.mp4")
                        truncated_video = video.subclip(0, self.max_video_length)
                        await write_videofile_async(truncated_video, filename=truncated_path,
                                                    logger=None, audio_codec="aac", fps=30)
                        video.close()
                        os.remove(video_path)  # 删除原始超长视频
                        logger.info(f"截取后的视频已保存到 {truncated_path}")
                        return truncated_path
            return video_path
        except Exception as e:
            logger.error(f"截取视频失败: {str(e)}")
            raise


async def main():
    weibo_title = '邓亚萍 莎莎的战术对方研究得非常透'
    weibo_crawler = WeiboCrawler()
    video_paths = await weibo_crawler.collect_videos(weibo_title, weibo_mid="123456")
    logger.info(f"已下载的视频文件: {video_paths}")


if __name__ == "__main__":
    asyncio.run(main())
