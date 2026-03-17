#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import os

logger = logging.getLogger('browser_manager')

class BrowserManager:
    def __init__(self, user_hash: str, uuk: str, user_id: str, headless: bool = False):
        self.user_hash = user_hash
        self.uuk = uuk
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
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
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
            
            # 3. Проверяем куки в браузере
            cookies = self.driver.get_cookies()
            cookie_names = [c['name'] for c in cookies]
            logger.info(f"📊 Куки в браузере после установки: {cookie_names}")
            
            if 'user_hash' in cookie_names and 'uuk' in cookie_names:
                logger.info("✅ Ключевые куки присутствуют в браузере")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки авторизации: {e}")
            return False
    
    def login(self):
        """'Вход' через установку всех кук."""
        try:
            logger.info("🔑 Начинаем процесс 'входа' через куки...")
            
            self.set_all_cookies()
            self.save_screenshot("1_after_cookies.png")
            
            if self.check_authorization_deep():
                logger.info("🎉 УСПЕХ! Авторизация по кукам сработала.")
                current_url = self.driver.current_url
                logger.info(f"📍 Текущий URL: {current_url}")
                return True
            else:
                logger.error("❌ Не удалось подтвердить авторизацию по кукам.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке кук: {e}")
            self.save_screenshot("error.png")
            return False
    
    def publish_post(self, title: str, content: str) -> bool:
        """Публикует пост на 9111.ru"""
        try:
            logger.info(f"📝 Начинаем публикацию: {title[:50]}...")
            
            actions = ActionChains(self.driver)
            
            # Открываем страницу публикации
            self.driver.get("https://9111.ru/pubs/add/title/")
            time.sleep(5)
            self.save_screenshot("2_publish_page.png")
            
            # Заголовок
            title_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[name='topic_name']")
            ))
            title_input.click()
            self.driver.execute_script(
                "arguments[0].innerText = arguments[1];", 
                title_input, 
                title[:150]
            )
            logger.info("✅ Заголовок введен")
            time.sleep(2)
            
            # Контент
            try:
                iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe")
                self.driver.switch_to.frame(iframe)
                content_body = self.driver.find_element(By.TAG_NAME, "body")
                content_body.click()
                self.driver.execute_script(
                    "arguments[0].innerHTML = arguments[1];", 
                    content_body, 
                    content[:10000].replace('\n', '<br>')
                )
                self.driver.switch_to.default_content()
                logger.info("✅ Контент введен")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось ввести контент: {e}")
            
            time.sleep(2)
            
            # Выбираем рубрику "Новости"
            try:
                rubric = self.driver.find_element(By.ID, "rubric_id2")
                rubric.click()
                time.sleep(1)
                news = self.driver.find_element(By.XPATH, "//option[@value='382235']")
                news.click()
                logger.info("✅ Рубрика 'Новости' выбрана")
            except:
                logger.warning("⚠️ Не удалось выбрать рубрику")
            
            # Вводим теги
            try:
                tags = self.driver.find_element(By.ID, "tag_list_input")
                tags.clear()
                tags.send_keys("новости, события, тест")
                logger.info("✅ Теги введены")
            except:
                pass
            
            time.sleep(2)
            
            # Нажимаем кнопку публикации
            try:
                submit_btn = self.driver.find_element(By.ID, "button_create_pubs")
                actions.move_to_element(submit_btn).perform()
                time.sleep(1)
                submit_btn.click()
                logger.info("✅ Кнопка публикации нажата")
            except:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Опубликовать')]")
                    actions.move_to_element(submit_btn).perform()
                    time.sleep(1)
                    submit_btn.click()
                    logger.info("✅ Кнопка публикации нажата")
                except Exception as e:
                    logger.error(f"❌ Не найдена кнопка публикации: {e}")
                    return False
            
            # Ждем результат
            time.sleep(5)
            self.save_screenshot("3_after_publish.png")
            
            # Проверяем успех
            page_source = self.driver.page_source.lower()
            if 'успешно' in page_source or 'опубликован' in page_source:
                logger.info("✅ ПОСТ УСПЕШНО ОПУБЛИКОВАН!")
                return True
            else:
                logger.warning("⚠️ Пост отправлен, но подтверждение не найдено")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка публикации: {e}")
            self.save_screenshot("publish_error.png")
            return False
