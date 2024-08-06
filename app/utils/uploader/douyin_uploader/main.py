# -*- coding: utf-8 -*-
from datetime import datetime

from loguru import logger
from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from app.utils.uploader.conf import LOCAL_CHROME_PATH
from app.utils.uploader.utils.base_social_media import set_init_script


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        # 2024.06.17 抖音创作者中心改版
        # 等待5秒钟
        await page.wait_for_timeout(5000)
        if await page.get_by_text('手机号登录').count():
            logger.warning("[+]   [Douyin] 等待5秒 cookie 失效")
            return False
        else:
            logger.success("[+]   [Douyin] cookie 有效")
            return True


async def douyin_setup(account_file, handle=False):
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await douyin_cookie_gen(account_file)
    return True


async def douyin_cookie_gen(account_file):
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class DouYinVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH

    async def set_schedule_time_douyin(self, page, publish_date):
        # 选择包含特定文本内容的 label 元素
        label_element = page.locator("label.radio--4Gpx6:has-text('定时发布')")
        # 在选中的 label 元素下点击 checkbox
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")

        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")

        await asyncio.sleep(1)

    async def handle_upload_error(self, page):
        logger.info('视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> bool:
        upload_ok = False
        # 使用 Chromium 浏览器启动一个浏览器实例
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=False, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=False)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        logger.info(f'[Douyin]正在上传-------{self.title}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        logger.info(f'[Douyin] 正在打开主页...')
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")
        # 点击 "上传视频" 按钮
        await page.locator('input[class^="upload-btn-input-"][type="file"]').set_input_files(self.file_path)

        # 等待页面跳转到指定的 URL
        while True:
            # 判断是是否进入视频发布页面，没进入，则自动等待到超时
            try:
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page")
                break
            except:
                logger.info(f'  [Douyin] 正在等待进入视频发布页面...')
                await asyncio.sleep(0.1)

        # 填充标题和话题
        # 检查是否存在包含输入框的元素
        # 这里为了避免页面变化，故使用相对位置定位：作品标题父级右侧第一个元素的input子元素
        await asyncio.sleep(1)
        logger.info(f'  [Douyin] 正在填充标题和话题...')
        title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator(
            "input")
        if await title_container.count():
            await title_container.fill(self.title[:30])
        else:
            titlecontainer = page.locator(".notranslate")
            await titlecontainer.click()
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(self.title)
            await page.keyboard.press("Enter")
        css_selector = ".zone-container"
        for index, tag in enumerate(self.tags, start=1):
            await page.type(css_selector, "#" + tag)
            await page.press(css_selector, "Space")
        logger.info(f'总共添加{len(self.tags)}个话题')

        while True:
            # 判断重新上传按钮是否存在，如果不存在，代表视频正在上传，则等待
            try:
                #  新版：定位重新上传
                number = await page.locator('div label+div:has-text("重新上传")').count()
                if number > 0:
                    logger.success("  [Douyin]视频上传完毕")
                    break
                else:
                    logger.info("  [Douyin] 正在上传视频中...")
                    await asyncio.sleep(2)

                    if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                        logger.error("  [-] 发现上传出错了... 准备重试")
                        await self.handle_upload_error(page)
            except:
                logger.info("  [Douyin] 正在上传视频中...")
                await asyncio.sleep(2)

        # 更换可见元素
        await page.locator('div.semi-select span:has-text("输入地理位置")').click()
        await asyncio.sleep(1)
        await page.keyboard.press("Backspace")
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.press("Delete")
        await page.keyboard.type("深圳市")
        # await asyncio.sleep(1)
        await page.wait_for_timeout(1000)
        await page.locator('div[role="listbox"] [role="option"]').first.click()

        # 頭條/西瓜
        third_part_element = '[class^="original-label"] div.semi-switch'
        # 定位是否有第三方平台
        if await page.locator(third_part_element).count():
            # 检测是否是已选中状态
            if 'semi-switch-checked' not in await page.eval_on_selector(third_part_element, 'div => div.className'):
                await page.locator(third_part_element).locator('input.semi-switch-native-control').click()

        if self.publish_date != 0:
            await self.set_schedule_time_douyin(page, self.publish_date)
        await asyncio.sleep(1.5)
        publish_attempt = 0
        # 判断视频是否发布成功
        while True:
            # 判断视频是否发布成功
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                    # 检查是否有提示上传次数达到上限
                    if await page.locator('span.semi-toast-content-text:has-text("今天投稿次数已达到上限")').count():
                        logger.warning("[Douyin] 达到上传次数上限，退出发布流程。")
                        await context.close()
                        await browser.close()
                        raise Exception("[Douyin] 达到上传次数上限，退出发布流程。")

                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/manage?enter_from=publish",
                                        timeout=1500)  # 如果自动跳转到作品页面，则代表发布成功
                logger.success("  [Douyin]视频发布成功")
                upload_ok = True
                break
            except:
                logger.info("  [Douyin] 视频正在发布中...")
                publish_attempt += 1
                await page.screenshot(full_page=True)
                await asyncio.sleep(0.5)
                if publish_attempt > 5:
                    logger.warning("  [Douyin] 发布超时...")
                    upload_ok = False
                    break
        await context.storage_state(path=self.account_file)  # 保存cookie
        logger.success('  [Douyin]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

        return upload_ok

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
