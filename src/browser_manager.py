#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import logging

logger = logging.getLogger('browser_manager')

class BrowserManager:
    def __init__(self, user_hash: str, uuk: str, user_id: str, headless: bool = False):
        self.user_hash = user_hash
        self.uuk = uuk
        self.user_id = user_id
        self.headless = headless
        self.driver = None
    
    def start(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Браузер запущен")
        return True
    
    def stop(self):
        if self.driver:
            self.driver.quit()
            logger.info("🛑 Браузер закрыт")
    
    def save_screenshot(self, name):
        self.driver.save_screenshot(name)
        logger.info(f"📸 Скриншот: {name}")
    
    def set_cookies(self):
        """Устанавливает куки для авторизации."""
        logger.info("🍪 Устанавливаем куки авторизации...")
        # Сначала нужно открыть домен, чтобы можно было установить куки
        self.driver.get("https://9111.ru")
        time.sleep(2)
        
        # Куки из вашего файла
        cookies = [
            {'name': 'user_hash', 'value': self.user_hash, 'domain': '.9111.ru'},
            {'name': 'uuk', 'value': self.uuk, 'domain': '.9111.ru'},
            # Можно добавить и другие куки, если нужно, но эти две — ключевые.
            # {'name': 'au', 'value': '{"u":2368040,"k":"aa8ca3729252da5450cdb0862352503d","t":1773721763}', 'domain': '.9111.ru'},
            # {'name': 'csrf_token', 'value': '{"token":"da7c5e304ead459418b7bcc8ac882ae70822a6660d9ee396240acf2581e129c3","ip":"5.44.168.228"}', 'domain': '.9111.ru'},
        ]
        
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
                logger.info(f"   Установлена кука: {cookie['name']}")
            except Exception as e:
                logger.warning(f"   Не удалось установить куку {cookie['name']}: {e}")
        
        logger.info("✅ Куки установлены")
        # После установки кук перезагрузим страницу
        self.driver.refresh()
        time.sleep(3)
    
    def check_authorization(self):
        try:
            page_source = self.driver.page_source
            if self.user_id in page_source:
                logger.info(f"✅ Найден ID пользователя {self.user_id}")
                return True
            return False
        except:
            return False
    
    def login(self):
        """'Вход' через установку кук."""
        try:
            logger.info("🔑 Начинаем процесс 'входа' через куки...")
            
            # Переходим на главную и устанавливаем куки
            self.set_cookies()
            self.save_screenshot("1_after_cookies.png")
            
            # Проверяем, авторизованы ли мы
            if self.check_authorization():
                logger.info("🎉 УСПЕХ! Авторизация по кукам сработала.")
                return True
            else:
                logger.error("❌ Не удалось подтвердить авторизацию по кукам.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке кук: {e}")
            self.save_screenshot("error.png")
            return False
