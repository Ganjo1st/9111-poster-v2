#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import time
from browser_manager import BrowserManager
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger('poster')

USER_HASH = os.getenv('USER_HASH')
UUK = os.getenv('UUK')
USER_ID = '2368040'

def main():
    logger.info("="*50)
    logger.info("🚀 ТЕСТОВЫЙ ЗАПУСК С ПУБЛИКАЦИЕЙ")
    logger.info("="*50)
    
    if not USER_HASH or not UUK:
        logger.error("❌ Не заданы USER_HASH или UUK в секретах!")
        sys.exit(1)
    
    logger.info(f"🆔 ID для проверки: {USER_ID}")
    
    browser = BrowserManager(
        user_hash=USER_HASH,
        uuk=UUK,
        user_id=USER_ID,
        headless=True
    )
    
    if not browser.start():
        logger.error("❌ Не удалось запустить браузер")
        sys.exit(1)
    
    # Вход через куки
    if not browser.login():
        logger.error("❌ Не удалось авторизоваться")
        browser.stop()
        sys.exit(1)
    
    # Тестовая публикация
    test_title = f"Тестовый пост от {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    test_content = f"""
    Это тестовый пост, созданный автоматически для проверки работы публикатора.
    
    Время создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ID пользователя: {USER_ID}
    
    Если вы это видите - значит публикатор работает правильно!
    
    Тестовое сообщение для проверки.
    """
    
    if browser.publish_post(test_title, test_content):
        logger.info("="*50)
        logger.info("✅ ТЕСТ ПРОЙДЕН - ПОСТ ОПУБЛИКОВАН!")
        logger.info("="*50)
    else:
        logger.error("="*50)
        logger.error("❌ ТЕСТ НЕ ПРОЙДЕН - ОШИБКА ПУБЛИКАЦИИ")
        logger.error("="*50)
    
    time.sleep(3)
    browser.stop()

if __name__ == "__main__":
    main()
