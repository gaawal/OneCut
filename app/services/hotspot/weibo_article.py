import asyncio
import os.path
import traceback

from loguru import logger
from playwright.async_api import async_playwright
import random

from app.utils import utils
from app.utils.utils import generate_md5_id


async def fetch_article_content_and_record(weibo_mid, url, video_path):
    logger.info(f"Fetching article content url is {url}")
    article_max = 20
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            record_video_size={"width": 1920, "height": 1080}
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
                introduction_element = page.locator('//*[@id="pl_feedlist_index"]/div[2]/div[1]/p')
                if await introduction_element.count() > 0:
                    introduction = await introduction_element.inner_text()
            except Exception as e:
                logger.warning(f"Introduction not found: {e}")

            # 提取热门评论
            await page.wait_for_selector('//div[@action-type="feed_list_item"]', timeout=1500)
            comment_elements = page.locator('//div[@action-type="feed_list_item"]')
            count = await comment_elements.count()

            for i in range(count):
                card_wrap = comment_elements.nth(i)
                nickname = (await card_wrap.locator('.name').first.inner_text()).strip()
                comment = (
                    await card_wrap.locator('p[node-type="feed_list_content"]').first.inner_text()).strip().replace(
                    "展开c", "")

                await card_wrap.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(1, 3))

                # 确保卡片可见且在页面范围内
                if await card_wrap.is_visible():
                    # 检查是否存在视频不支持播放的提示框
                    if await card_wrap.locator(
                            '[node-type="feed_list_media_prev"] .wbpv-error-display.wbpv-modal-dialog').count() > 0:
                        continue

                    # 截图当前卡片区域
                    bounding_box = await card_wrap.bounding_box()
                    if bounding_box:
                        screenshot_path = os.path.join(video_path, f"{weibo_mid}-card_screenshot_{i}.png")
                        await page.screenshot(path=screenshot_path, clip=bounding_box)

                        article = {
                            "nickname": nickname,
                            "comment": comment,
                            "screenshot": screenshot_path,
                            "images": []
                        }

                        # 查找图片列表容器并点击缩略图
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
                                            timeout=1000)
                                        await asyncio.sleep(1)  # 等待大图加载

                                        # 查找并处理展开的图片容器，仅在当前card_wrap范围内
                                        big_image_selector = '[node-type="feed_list_media_disp"] [node-type="imagesBox"] [node-type="picShow"] [node-type="imgBox"] img'
                                        big_image_elements = card_wrap.locator(big_image_selector)
                                        big_image_count = await big_image_elements.count()
                                        for k in range(big_image_count):
                                            big_image = big_image_elements.nth(k)
                                            if await big_image.is_visible():
                                                await big_image.scroll_into_view_if_needed()
                                                bounding_box = await big_image.bounding_box()
                                                big_image_path = os.path.join(video_path,
                                                                              f"{weibo_mid}-big_image_{i}_{j}_{k}.png")
                                                await page.screenshot(path=big_image_path, clip=bounding_box)

                                                article["images"].append(big_image_path)

                                        # 关闭大图
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
            logger.debug(traceback.format_exc())

        # 关闭页面和浏览器
        await page.close()
        await context.close()
        await browser.close()

        return introduction, articles


async def fetch_hot_article(hot_url):
    weibo_mid = generate_md5_id(hot_url)
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
    hot_url = 'https://s.weibo.com/weibo?q=%23%E5%86%85%E9%A9%AC%E5%B0%94%23'
    weibo_article_data = await fetch_hot_article(weibo_mid, hot_url)

    print(generate_weibo_summary(weibo_article_data, 10))


if __name__ == '__main__':
    asyncio.run(main())
