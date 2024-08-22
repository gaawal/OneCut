import asyncio
import json
import os.path
import traceback
from datetime import datetime
from typing import List, Tuple

from loguru import logger
from playwright.async_api import async_playwright
import random

from app.constant.video_const import CollectStatus
from app.services.redis_service import redis_instance
from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.schemas.movies import WeiboArticleData, WeiboArticle
from app.utils import utils
from app.utils.crawler.weibo_crawler.main import weibo_setup
from pathlib import Path


async def fetch_article_content_and_record(weibo_mid: str, url: str, video_path: str) -> Tuple[str, List[WeiboArticle]]:
    BASE_DIR = Path(__file__).parent.resolve()
    base_dir = Path(BASE_DIR)
    cookie_file = 'WeiboCookie.json'
    cookie_file = os.path.join(base_dir, cookie_file)
    if not await weibo_setup(str(cookie_file), handle=False):
        logger.error("微博未登录，无法获取数据")
        return
    logger.info(f"开始采集微博热搜链接： {url}")
    article_max = 20
    current_time = datetime.now()
    formatted_time_str = current_time.strftime("%Y%m%d%H%M")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            record_video_size={"width": 1920, "height": 1080},
            storage_state=cookie_file
        )
        await context.add_init_script(path="libs/stealth.min.js")
        page = await context.new_page()
        await page.goto(url)
        await asyncio.sleep(5)
        introduction = ""
        articles = []
        try:
            # 尝试提取导语
            try:
                logger.info("提取导语ing")
                introduction_element = page.locator('//*[@id="pl_feedlist_index"]/div[2]/div[1]/p')
                if await introduction_element.count() > 0:
                    introduction = await introduction_element.inner_text()
                    logger.info(f"{introduction}")
            except Exception as e:
                logger.warning(f"Introduction not found: {e}")

            # 提取热门评论
            await page.wait_for_selector('//div[@action-type="feed_list_item"]', timeout=1500)
            comment_elements = page.locator('//div[@action-type="feed_list_item"]')
            count = await comment_elements.count()
            logger.info(f"提取热门评论有{count}条")
            for i in range(count):

                card_wrap = comment_elements.nth(i)
                nickname = (await card_wrap.locator('.name').first.inner_text()).strip()
                comment = (
                    await card_wrap.locator('p[node-type="feed_list_content"]').first.inner_text()).strip()
                logger.info(f"{i + 1}、网友[{nickname}」热门评论:{comment}")
                article = WeiboArticle(
                    nickname=nickname,
                    comment=comment,
                    screenshot_path="",
                    images=[]
                )
                await card_wrap.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(1, 3))

                if await card_wrap.is_visible():
                    if await card_wrap.locator(
                            '[node-type="feed_list_media_prev"] .wbpv-error-display.wbpv-modal-dialog').count() > 0:
                        continue

                    bounding_box = await card_wrap.bounding_box()
                    if bounding_box:
                        card_screenshot = os.path.join(video_path,
                                                       f"{formatted_time_str}-{weibo_mid}-card_screenshot_{i}.png")
                        await page.screenshot(path=card_screenshot, clip=bounding_box)
                        article.screenshot_path = card_screenshot
                        logger.info(f"{i + 1}、保存评论截图：{card_screenshot}")
                        try:
                            if await card_wrap.locator(
                                    '[node-type="feed_list_media_prev"] [node-type="fl_pic_list"]').is_visible():
                                thumbnails = card_wrap.locator(
                                    '[node-type="feed_list_media_prev"] [node-type="fl_pic_list"] ul li')
                                thumbnail_count = await thumbnails.count()
                                for j in range(thumbnail_count):
                                    thumbnail = thumbnails.nth(j)
                                    if await thumbnail.is_visible():
                                        await thumbnail.scroll_into_view_if_needed()
                                        await thumbnail.click(timeout=1500)
                                        await page.wait_for_selector(
                                            '[node-type="feed_list_media_disp"] [node-type="imagesBox"] [node-type="picShow"] [node-type="imgBox"] img',
                                            timeout=1500)
                                        await asyncio.sleep(1)

                                        big_image_selector = '[node-type="feed_list_media_disp"] [node-type="imagesBox"] [node-type="picShow"] [node-type="imgBox"] img'
                                        big_image_elements = card_wrap.locator(big_image_selector)
                                        big_image_count = await big_image_elements.count()
                                        for k in range(big_image_count):
                                            big_image = big_image_elements.nth(k)
                                            if await big_image.is_visible():
                                                await big_image.scroll_into_view_if_needed()
                                                bounding_box = await big_image.bounding_box()

                                                big_image_path = os.path.join(video_path,
                                                                              f"{formatted_time_str}-{weibo_mid}-big_image_{i}_{j}_{k}.png")
                                                await page.screenshot(path=big_image_path, clip=bounding_box)
                                                article.images.append(big_image_path)
                                                logger.info(f"{i + 1}、保存评论大图：{big_image_path}")
                                        close_button = card_wrap.locator(
                                            '[node-type="imagesBox"] [action-type="tosmall"]')
                                        if await close_button.is_visible():
                                            await close_button.click()
                                        await asyncio.sleep(1)
                        except Exception as e:
                            logger.warning(f"Image not found or clickable: {e}")

                if len(articles) < article_max:
                    articles.append(article)
            logger.info(f"{url}获取文章数： {len(articles)}")
        except Exception as e:
            logger.error(traceback.format_exc())

        await page.close()
        await context.close()
        await browser.close()

        return introduction, articles


async def fetch_hot_article(weibo_article_data: WeiboArticleData, weibo_mid, target_url) -> WeiboArticleData:
    articles = []
    introduction = ''
    video_dir = utils.cache_browser_info_dir()
    try:
        introduction, articles = await fetch_article_content_and_record(weibo_mid, target_url, video_dir)
    except Exception as ex:
        logger.error(f"fetch_article_content_and_record error ,because {traceback.format_exc()}")
    if articles:
        weibo_article_data.articles = articles
        weibo_article_data.introduction = introduction
    else:
        logger.warning("获取微博文章内容信息缺失")
    return weibo_article_data


def generate_weibo_summary(data: WeiboArticleData ):
    num_comments = 7
    introduction = data.introduction if hasattr(data, 'introduction') else None
    articles = data.articles
    summary = ""
    if introduction:
        summary += introduction + "\n\n"
    summary += "主题相关信息：\n"
    for i, article in enumerate(articles[:num_comments]):
        summary += f"{i + 1}.{article.comment}\n"
    return summary


async def save_weibo_article_and_update_data(weibo_title: str, weibo_article_cache: WeiboArticleData,collect_status=CollectStatus.COLLECTING):
    """
    保存话题内容到缓存中，同时刷新微博已采集的话题数据
    """
    if weibo_article_cache:
        weibo_article_json = json.dumps(weibo_article_cache.dict(), ensure_ascii=False)
        await redis_instance.set(
            RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(weibo_title),
            weibo_article_json,
            expire=RedisExpireTime.ONE_DAY)

        hot_data = await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_SEARCH)
        if hot_data:
            hot_data = json.loads(hot_data)
            for i, item in enumerate(hot_data):
                if weibo_title == item.get('title'):
                    hot_data[i]["collect_status"] = collect_status
            await redis_instance.set(
                RedisKeyPrefix.WEIBO_HOT_SEARCH,
                json.dumps(hot_data, ensure_ascii=False),
                expire=RedisExpireTime.THIRTY_MINUTES
            )
        return True
    return False


async def update_weibo_generated_state(weibo_title):
    if cached_data := await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(weibo_title)):
        weibo_article_cache = json.loads(cached_data)
        weibo_article_cache = WeiboArticleData(**weibo_article_cache)
        weibo_article_cache.is_generated = True
        weibo_article_json = json.dumps(weibo_article_cache.dict(), ensure_ascii=False)
        await redis_instance.set(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(weibo_title), weibo_article_json,
                                 expire=RedisExpireTime.ONE_DAY)

    pass


async def main():
    weibo_mid = "example_mid"  # Replace with the actual weibo_mid
    hot_url = 'https://s.weibo.com/weibo?q=%23%E5%86%85%E9%A9%AC%E5%B0%94%23'
    weibo_article_data = await fetch_hot_article(hot_url)

    print(generate_weibo_summary(weibo_article_data, 10))


if __name__ == '__main__':
    asyncio.run(main())
