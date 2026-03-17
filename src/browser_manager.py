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
        
        # Реальные заголовки браузера
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--accept-lang=ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7")
        chrome_options.add_argument("--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
        
        # Скрываем автоматизацию
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
        # Дополнительно скрываем webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
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
            
            # Сначала заходим на главную с паузой
            self.driver.get("https://9111.ru/")
            time.sleep(5)
            self.save_screenshot("1_main_page.png")
            
            # Даже если 403, пробуем зайти на логин
            logger.info("🌐 Переходим на страницу логина...")
            self.driver.get("https://9111.ru/login/")
            time.sleep(5)
            self.save_screenshot("2_login_page.png")
            
            # Пробуем найти поля ввода разными способами
            try:
                # Способ 1: по name
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
            except:
                try:
                    # Способ 2: по CSS селектору
                    email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                except:
                    try:
                        # Способ 3: по placeholder
                        email_input = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'mail') or contains(@placeholder, 'логин')]")
                    except Exception as e:
                        logger.error(f"❌ Не удалось найти поле email: {e}")
                        return False
            
            email_input.clear()
            email_input.send_keys(self.email)
            logger.info("✅ Email введен")
            time.sleep(1)
            
            # Ищем поле пароля
            try:
                password_input = self.driver.find_element(By.NAME, "password")
            except:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                except Exception as e:
                    logger.error(f"❌ Не удалось найти поле пароля: {e}")
                    return False
            
            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("✅ Пароль введен")
            time.sleep(1)
            
            # Ищем кнопку входа
            try:
                submit = self.driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
            except:
                try:
                    submit = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Войти') or contains(text(), 'Вход')]")
                except Exception as e:
                    logger.error(f"❌ Не удалось найти кнопку входа: {e}")
                    return False
            
            submit.click()
            logger.info("✅ Кнопка входа нажата")
            
            # Ждем результат
            time.sleep(7)
            self.save_screenshot("3_after_login.png")
            
            # Проверяем авторизацию
            if self.check_authorization():
                logger.info("🎉 ВХОД ВЫПОЛНЕН УСПЕШНО!")
                return True
            else:
                logger.error("❌ Вход не удался")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            self.save_screenshot("error.png")
            return False
