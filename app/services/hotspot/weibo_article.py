import asyncio
import os.path
import traceback

from loguru import logger
from playwright.async_api import async_playwright
import random

from app.utils import utils

async def fetch_article_content_and_record(weibo_mid, url, video_path):
    logger.info(f"Fetching article content url is {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # 无头浏览器
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            record_video_dir=video_path,
            record_video_size={"width": 1920, "height": 1080}
        )

        page = await context.new_page()
        await page.goto(url)
        introduction = ""
        articles = []
        try:
            # 尝试提取导语
            try:
                introduction_element = page.locator('//*[@id="pl_feedlist_index"]/div[2]/div[1]/p')
                if await introduction_element.count() > 0:
                    introduction = await introduction_element.inner_text()
            except Exception as e:
                logger.warning(f"Introduction not found: {e}")

            # 提取热门评论
            await page.wait_for_selector('//div[@action-type="feed_list_item"]', timeout=15000)
            comment_elements = page.locator('//div[@action-type="feed_list_item"]')
            count = await comment_elements.count()

            for i in range(count):
                card_wrap = comment_elements.nth(i)
                nickname = (await card_wrap.locator('.name').inner_text()).strip()
                comment = (await card_wrap.locator('p[node-type="feed_list_content"]').inner_text()).strip().replace("展开c", "")

                await card_wrap.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(1, 3))  # 确保页面加载完全

                # 确保卡片可见且在页面范围内
                if await card_wrap.is_visible():
                    # 截图当前卡片区域
                    bounding_box = await card_wrap.bounding_box()
                    if bounding_box:
                        screenshot_path = os.path.join(video_path, f"{weibo_mid}-card_screenshot_{i}.png")
                        await page.screenshot(path=screenshot_path, clip=bounding_box)

                        # 添加到文章列表
                        articles.append({
                            "nickname": nickname,
                            "comment": comment,
                            "screenshot": screenshot_path
                        })
                        logger.success(f"Success fetch weibo comment:{comment}\nscreenshot:{screenshot_path}")
        except Exception as e:
            logger.error(f"Error fetching article content: {e}")
            logger.debug(traceback.format_exc())

        # 关闭页面和浏览器
        await page.close()
        await context.close()
        await browser.close()

        return introduction, articles

async def fetch_hot_article(weibo_mid, hot_url):
    # 定位至实际的热门
    target_url = f'{hot_url}'
    video_dir = utils.cache_browser_info_dir()
    introduction, articles = await fetch_article_content_and_record(weibo_mid, target_url, video_dir)

    weibo_article_data = {
        "weibo_mid": weibo_mid,
        "url": target_url,
        "introduction": introduction,
        "articles": articles
    }
    return weibo_article_data

def generate_weibo_summary(data, num_comments):
    introduction = data["introduction"]
    articles = data["articles"]
    summary = ""
    if introduction:
        summary += introduction + "\n\n"
    summary += "主题相关信息：\n"
    for i, article in enumerate(articles[:num_comments]):
        summary += f"{i + 1}.{article['comment']}\n"
    return summary

async def main():
    weibo_mid = "example_mid"  # Replace with the actual weibo_mid
    hot_url = 'https://s.weibo.com/weibo?q=%23吴昕 陈昊宇依然需要自我介绍%23'
    weibo_article_data = await fetch_hot_article(weibo_mid, hot_url)
    print(generate_weibo_summary(weibo_article_data, 10))

if __name__ == '__main__':
    asyncio.run(main())
