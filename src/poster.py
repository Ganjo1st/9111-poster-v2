#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import time
from browser_manager import BrowserManager

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
    logger.info("🚀 ТЕСТОВЫЙ ЗАПУСК")
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
    
    if browser.login():
        logger.info("="*50)
        logger.info("✅ ТЕСТ ПРОЙДЕН")
        logger.info("="*50)
    else:
        logger.error("="*50)
        logger.error("❌ ТЕСТ НЕ ПРОЙДЕН")
        logger.error("="*50)
    
    time.sleep(2)
    browser.stop()

if __name__ == "__main__":
    main()
