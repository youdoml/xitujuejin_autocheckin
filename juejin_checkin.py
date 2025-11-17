import asyncio
import json
from playwright.async_api import async_playwright
import schedule
import time
from datetime import datetime
import logging
import os

filename =os.path.join(os.path.dirname(__file__), "juejin_cookies.log")
# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=filename, encoding='utf-8')
logger = logging.getLogger(__name__)

class JuejinCheckin:
    def __init__(self, username=None, password=None, cookies_file='juejin_cookies.json'):
        self.username = username
        self.password = password
        self.cookies_file = cookies_file
        
    async def load_cookies(self, context):
        """从文件加载cookies"""
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                logger.info("Cookies loaded successfully")
                return True
        except FileNotFoundError:
            logger.warning("Cookies file not found")
            return False
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
            
    async def save_cookies(self, context):
        """保存cookies到文件"""
        try:
            cookies = await context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
                logger.info("Cookies saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            
    async def login_manually(self, page, context):
        """手动登录获取cookies"""
        logger.info("请在浏览器中手动登录稀土掘金...")
        await page.goto("https://juejin.cn/")
        # 等待用户登录
        await page.wait_for_timeout(120000)  # 等待60秒用于登录
        await self.save_cookies(context)
        
    async def checkin(self, page):
        """执行签到操作"""
        try:
            # 访问掘金主页
            await page.goto("https://juejin.cn/")
            # await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(10000)
            # 检查是否已登录
            login_button = page.locator(".login-button:first-child")
            if await login_button.is_visible():
                logger.error("未登录，请先登录")
                return False
                
            # 点击签到按钮
            checkin_button = page.get_by_role("button", name="签到")

            if await checkin_button.is_visible():
                await checkin_button.click()
                logger.info("点击签到按钮成功")
                # 点击立即签到
                
                logger.info("等待页面加载")
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(5000)

                immediate_checkin_button = page.get_by_role("button", name="立即签到")
                if await immediate_checkin_button.is_visible():
                    await immediate_checkin_button.click()
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(5000)
                    # logger.info("签到成功")
                    # 保存签到后的cookies

                    is_checked_in = page.get_by_role("button", name="已签到")
                    if await is_checked_in.is_visible():
                        logger.info("已签到")
                    else:
                        logger.info("签到失败")

                    return True
                else:
                    logger.info("可能已经签到过了")
                    return True
            else:
                logger.info("签到按钮不可见，可能已经签到过了")
                return True
                
        except Exception as e:
            logger.error(f"签到过程中出现错误: {e}")
            return False
            
    async def run_checkin(self):
        """运行签到流程"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            
            # 加载cookies
            cookies_loaded = await self.load_cookies(context)
            
            page = await context.new_page()
            
            if not cookies_loaded:
                # 如果没有cookies，则需要手动登录
                logger.info('没有加载到cookie')
                await self.login_manually(page, context)
            
            # 执行签到
            success = await self.checkin(page)
            
            for i in range(5):
                if not success:
                    logger.error(f"签到失败{i}")
                    await asyncio.sleep(10 + i * 10 * 60)
                    success = await self.checkin(page)
                else:
                    logger.info("今日签到已完成")
                    break
                
                
            await self.save_cookies(context)
            
            # 关闭浏览器
            await browser.close()

def job():
    """定时任务执行函数"""
    logger.info("开始执行签到任务")
    checkin = JuejinCheckin()
    asyncio.run(checkin.run_checkin())

if __name__ == "__main__":
    # 立即执行一次签到
    # job()
    
    # # 设置每日定时任务
    # schedule.every().day.at("09:00").do(job)
    
    # logger.info("稀土掘金签到服务已启动，将在每天09:00自动签到")
    
    # # 保持程序运行
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
    cookies_file = os.path.join(os.path.dirname(__file__), "juejin_cookies.json")
    logger.info('加载cookies file' + cookies_file)
    checkin =JuejinCheckin(cookies_file=cookies_file)
    asyncio.run(checkin.run_checkin())