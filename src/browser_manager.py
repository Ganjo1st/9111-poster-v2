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
    
    def set_all_cookies(self):
        """Устанавливает ВСЕ куки из предоставленного файла."""
        logger.info("🍪 Устанавливаем ВСЕ куки авторизации...")
        
        # Сначала открываем домен, чтобы можно было установить куки
        self.driver.get("https://9111.ru")
        time.sleep(3)
        
        # ВСЕ куки из вашего файла
        all_cookies = [
            {'name': 'user_hash', 'value': self.user_hash, 'domain': '.9111.ru', 'path': '/', 'secure': True},
            {'name': 'uuk', 'value': self.uuk, 'domain': '.9111.ru', 'path': '/', 'secure': True},
            {'name': 'geo', 'value': '91-817-1', 'domain': '.9111.ru', 'path': '/', 'secure': True},
            {'name': 'tmp_url_redirect', 'value': 'https%3A%2F%2F9111.ru%2F', 'domain': '.9111.ru', 'path': '/', 'secure': True},
            {'name': 'csrf_token', 'value': '{"token":"da7c5e304ead459418b7bcc8ac882ae70822a6660d9ee396240acf2581e129c3","ip":"5.44.168.228"}', 'domain': '.9111.ru', 'path': '/', 'secure': True},
            {'name': 'au', 'value': '{"u":2368040,"k":"aa8ca3729252da5450cdb0862352503d","t":1773721763}', 'domain': '.9111.ru', 'path': '/', 'secure': True}
        ]
        
        for cookie in all_cookies:
            try:
                self.driver.add_cookie(cookie)
                logger.info(f"   ✅ Установлена кука: {cookie['name']}")
            except Exception as e:
                logger.warning(f"   ⚠️ Не удалось установить куку {cookie['name']}: {e}")
        
        logger.info("✅ Все куки установлены")
        
        # Обновляем страницу
        self.driver.refresh()
        time.sleep(5)
    
    def check_authorization_deep(self):
        """Глубокая проверка авторизации по нескольким признакам"""
        try:
            page_source = self.driver.page_source
            
            # 1. Проверяем наличие ID пользователя
            if self.user_id in page_source:
                logger.info(f"✅ Найден ID пользователя {self.user_id}")
                return True
            
            # 2. Проверяем наличие индикаторов авторизации
            auth_indicators = [
                'Выход',
                'Мои публикации',
                'Баланс',
                'Профиль',
                'userMenuOpen',
                'notification-bell'
            ]
            
            for indicator in auth_indicators:
                if indicator in page_source:
                    logger.info(f"✅ Найден индикатор авторизации: '{indicator}'")
                    return True
            
            # 3. Проверяем куки в браузере (те, что установились)
            cookies = self.driver.get_cookies()
            cookie_names = [c['name'] for c in cookies]
            logger.info(f"📊 Куки в браузере после установки: {cookie_names}")
            
            # Проверяем наличие ключевых кук
            if 'user_hash' in cookie_names and 'uuk' in cookie_names:
                logger.info("✅ Ключевые куки присутствуют в браузере")
                # Если куки есть, но ID не найден, возможно, страница не та
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки авторизации: {e}")
            return False
    
    def login(self):
        """'Вход' через установку всех кук."""
        try:
            logger.info("🔑 Начинаем процесс 'входа' через куки...")
            
            # Устанавливаем ВСЕ куки
            self.set_all_cookies()
            self.save_screenshot("1_after_all_cookies.png")
            
            # Проверяем авторизацию
            if self.check_authorization_deep():
                logger.info("🎉 УСПЕХ! Авторизация по кукам сработала.")
                
                # Дополнительно проверяем, что мы действительно на сайте
                current_url = self.driver.current_url
                logger.info(f"📍 Текущий URL: {current_url}")
                
                return True
            else:
                logger.error("❌ Не удалось подтвердить авторизацию по кукам.")
                
                # Сохраняем HTML для анализа
                with open("page_source.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.info("💾 Сохранен HTML страницы для анализа")
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке кук: {e}")
            self.save_screenshot("error.png")
            return False
