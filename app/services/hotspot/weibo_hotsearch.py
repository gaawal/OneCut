import asyncio
import traceback
import requests
import random
from loguru import logger


async def get_weibo_hotsearch():
    hotsearch_data = []
    logger.info("微博数据采集ing")
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://weibo.com/"
        }

        # 随机延迟以避免检测
        await asyncio.sleep(random.uniform(2, 5))
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            raw_data = response.json().get('data', {})
            hotsearch_data = []
            for item in raw_data.get('realtime', {}):
                if item.get("mid") != 0:
                    hotsearch_data.append({
                        "mid": item.get("mid"),  # 热搜id
                        "category": item.get("category"),
                        "title": item.get("note"),
                        "hot": item.get("num"),
                        "url": f"https://s.weibo.com/weibo?q=%23{item.get('note')}%23",
                    })

            logger.success("Weibo data saved redis successfully.")
        else:
            logger.error("Failed to retrieve data.")
    except Exception as e:
        logger.error(f"Failed to retrieve data. {traceback.format_exc()}")
    return hotsearch_data
