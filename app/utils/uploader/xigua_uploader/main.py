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
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://studio.ixigua.com/upload")
        if await page.get_by_text('登录 / 注册').count():
            print("[Xigua] 等待5秒 cookie 失效")
            return False
        else:
            logger.success("[Xigua] cookie 有效")
            return True


async def xigua_setup(account_file, handle=False):
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        logger.info('[Xigua] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await xigua_cookie_gen(account_file)
    return True


async def xigua_cookie_gen(account_file):
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
        await page.goto("https://studio.ixigua.com/")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class XiguaVideo(object):
    def __init__(self, title, file_path, tags, cover_image,publish_date: datetime, account_file):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.cover_image = cover_image
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH

    async def set_schedule_time_xigua(self, page, publish_date):
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
            browser = await playwright.chromium.launch(headless=True, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=True)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://studio.ixigua.com/upload")
        logger.info(f'[Xigua]正在上传-------{self.title}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        logger.info(f'[Xigua] 正在打开主页...')
        await page.wait_for_url("https://studio.ixigua.com/upload")
        # 点击 "上传视频" 按钮
        await page.locator('input[type="file"]').set_input_files(self.file_path)
        # 填充标题和话题
        # 检查是否存在包含输入框的元素
        # 这里为了避免页面变化，故使用相对位置定位：作品标题父级右侧第一个元素的input子元素
        await asyncio.sleep(1)
        # 填充标题和话题
        await asyncio.sleep(1)
        logger.info(f'  [Xigua] 正在填充标题和话题...')
        title_container = page.locator('div.mentionText').first
        await title_container.click()
        await page.keyboard.press("Backspace")
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.press("Delete")
        await page.keyboard.type(self.title)

        css_selector = page.locator('input.arco-input-tag-input').first
        for index, tag in enumerate(self.tags, start=1):
            await css_selector.fill("#" + tag)
            logger.info(f'添加话题:{tag}')
            await asyncio.sleep(1)
            await page.keyboard.press("Space")
            await asyncio.sleep(1)
        logger.info(f'总共添加{len(self.tags)}个话题')

        # 点击弹窗中的 "下一步" 按钮
        logger.info('  [Xigua] 正在勾选原创按钮...')
        next_button = page.locator('span.byte-radio-inner-text:has-text("原创")')
        await next_button.wait_for(timeout=5000)
        await next_button.click()
        await asyncio.sleep(2)

        # 点击 "上传封面" 按钮
        logger.info('  [Xigua] 正在点击上传封面按钮...')
        await page.locator('text=上传封面').click()
        await asyncio.sleep(2)

        # 点击弹窗中的 "下一步" 按钮
        logger.info('  [Xigua] 正在点击弹窗中的本地上传...')
        next_button = page.locator('text=本地上传')
        await next_button.wait_for(timeout=5000)
        await next_button.click()
        await asyncio.sleep(2)

        # 点击弹窗中的 "下一步" 按钮
        logger.info('  [Xigua] 正在上传封面图片...')
        await page.locator('input[type="file"]').set_input_files(self.cover_image)
        await asyncio.sleep(2)

        # 点击提示框中的 "确定" 按钮
        logger.info('  [Xigua] 正在点击提示框中的确定按钮...')
        confirm_button = page.locator('text=确定')
        await confirm_button.wait_for()
        await confirm_button.click()
        await asyncio.sleep(2)

        # 点击提示框中的第二个 "确定" 按钮
        logger.info('  [Xigua] 正在点击提示框中的第二个确定按钮...')
        confirm_button_red = page.locator('button.m-button.red').nth(1)
        await confirm_button_red.wait_for()
        await confirm_button_red.click()
        await asyncio.sleep(2)

        while True:
            # 判断重新上传按钮是否存在，如果不存在，代表视频正在上传，则等待
            try:
                #  新版：根据 class="success" 和文本内容 "上传成功" 进行判断
                number = await page.locator('text=上传成功').count()
                if number > 0:
                    logger.success("  [Xigua]视频上传完毕")
                    upload_ok = True
                    break
                else:
                    logger.info("  [Xigua] 正在上传视频中...")
                    await asyncio.sleep(2)
                    if await page.locator('text=上传失败').count():
                        logger.error("  [Xigua] 发现上传出错了... 准备重试")
                        await self.handle_upload_error(page)
            except:
                logger.info("  [Xigua] 正在上传视频中...")
                await asyncio.sleep(2)


        if self.publish_date != 0:
            await self.set_schedule_time_xigua(page, self.publish_date)
        await asyncio.sleep(1.5)
        # 判断视频是否发布成功
        publish_attempt = 0
        while True:
            # 判断视频是否发布成功
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                    pass
                await page.wait_for_url("https://studio.ixigua.com/content**",
                                        timeout=1500)  # 如果自动跳转到作品页面，则代表发布成功
                logger.success("  [Xigua]视频发布成功")
                break
            except:
                logger.info("  [Xigua] 视频正在发布中...")
                publish_attempt += 1
                await page.screenshot(full_page=True)
                await asyncio.sleep(0.5)
                if publish_attempt > 10:
                    raise Exception(" [Xigua] 发布超时...")

        await context.storage_state(path=self.account_file)  # 保存cookie
        logger.success('  [Xigua]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()
        return upload_ok
    async def main(self):
        try:
            async with async_playwright() as playwright:
                return await self.upload(playwright)
        except Exception as e:
            logger.warning(f"  [Douyin] 发布出现异常,{str(e)}")
            return False


