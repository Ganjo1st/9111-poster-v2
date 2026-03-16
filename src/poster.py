import os
import sys
import logging
from browser_manager import BrowserManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('poster')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NINTH_EMAIL = os.getenv('NINTH_EMAIL')
NINTH_PASSWORD = os.getenv('NINTH_PASSWORD')
USER_ID = '2368040'

def main():
    logger.info("="*50)
    logger.info("ТЕСТОВЫЙ ЗАПУСК")
    logger.info("="*50)
    
    browser = BrowserManager(NINTH_EMAIL, NINTH_PASSWORD, USER_ID, headless=True)
    
    if not browser.start():
        logger.error("Не удалось запустить браузер")
        return
    
    if browser.login():
        logger.info("✅ ТЕСТ ПРОЙДЕН - АВТОРИЗАЦИЯ РАБОТАЕТ!")
    else:
        logger.error("❌ ТЕСТ НЕ ПРОЙДЕН")
    
    browser.stop()

if __name__ == "__main__":
    main()
