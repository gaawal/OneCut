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
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://weibo.com/")
        #
        await page.wait_for_timeout(5000)
        if await page.get_by_text('扫描二维码登录').count():
            logger.warning("[+]   [Weibo] cookie 失效，需要扫描二维码登录")
            return False
        else:
            logger.success("[+]   [Weibo] cookie 有效")
            return True


async def weibo_setup(cookie_file, handle=False):
    if not os.path.exists(cookie_file) or not await cookie_auth(cookie_file):
        if not handle:
            return False
        logger.info('[Weibo] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await weibo_cookie_gen(cookie_file)
    return True


async def weibo_cookie_gen(account_file):
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
        await page.goto("https://passport.weibo.com/sso/signin?entry=account&source=sinassopage")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)



