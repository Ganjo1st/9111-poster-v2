#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import logging

logger = logging.getLogger('browser_manager')

class BrowserManager:
    def __init__(self, email: str, password: str, user_id: str, headless: bool = False):
        self.email = email
        self.password = password
        self.user_id = user_id
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def start(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("✅ Браузер запущен")
        return True
    
    def stop(self):
        if self.driver:
            self.driver.quit()
            logger.info("🛑 Браузер закрыт")
    
    def save_screenshot(self, name):
        self.driver.save_screenshot(name)
        logger.info(f"📸 Скриншот: {name}")
    
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
        try:
            logger.info("🔑 Вход на сайт...")
            
            self.driver.get("https://9111.ru/")
            time.sleep(3)
            self.save_screenshot("1_main_page.png")
            
            # Проверяем не заблокирован ли доступ
            if "403" in self.driver.title or "Forbidden" in self.driver.page_source:
                logger.error("❌ Доступ заблокирован (403 Forbidden)")
                return False
            
            # Пробуем перейти на страницу логина
            self.driver.get("https://9111.ru/login/")
            time.sleep(3)
            self.save_screenshot("2_login_page.png")
            
            if "403" in self.driver.title or "Forbidden" in self.driver.page_source:
                logger.error("❌ Страница логина заблокирована")
                return False
            
            # Ищем поля ввода
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys(self.email)
            
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(self.password)
            
            submit = self.driver.find_element(By.XPATH, "//input[@type='submit']")
            submit.click()
            
            time.sleep(5)
            self.save_screenshot("3_after_login.png")
            
            if self.check_authorization():
                logger.info("✅ Вход выполнен успешно!")
                return True
            else:
                logger.error("❌ Вход не удался")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            self.save_screenshot("error.png")
            return False
