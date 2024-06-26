import traceback

from playwright.sync_api import sync_playwright
import json
import time

def fetch_article_content_and_record(url, video_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 显示浏览器窗口
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            record_video_dir=video_path,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.goto(url)
        try:
            # 等待内容加载
            page.wait_for_selector('div.card-wrap')

            # 模拟滚动浏览并截图
            articles = []
            card_wraps = page.locator('div.card-wrap')
            count = card_wraps.count()
            screenshots = []

            for i in range(count):
                # 定位到当前卡片
                card_wrap = card_wraps.nth(i)
                card_wrap.scroll_into_view_if_needed()
                time.sleep(1)  # 确保页面加载完全

                # 确保卡片可见且在页面范围内
                if card_wrap.is_visible():
                    # 截图当前卡片区域
                    bounding_box = card_wrap.bounding_box()
                    if bounding_box:
                        screenshot_path = f"{video_path}/card_screenshot_{i}.png"
                        page.screenshot(path=screenshot_path, clip=bounding_box)
                        screenshots.append(screenshot_path)

                        # 提取内容
                        article_content = card_wrap.inner_text()
                        articles.append({
                            "content": article_content
                        })
                        print(f"article_content:{article_content}\n")
        except:
            print(traceback.format_exc())

        # 关闭页面和浏览器
        page.close()
        context.close()
        browser.close()

        return articles, screenshots

def main():
    target_url = 'https://s.weibo.com/weibo?q=%23杨幂发表C刊%23'
    video_dir = './videos'
    article_content, screenshots = fetch_article_content_and_record(target_url, video_dir)

    data = {
        "url": target_url,
        "articles": article_content,
        "screenshots": screenshots
    }

    with open('weibo_article_details.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("Data saved successfully.")

if __name__ == '__main__':
    main()
