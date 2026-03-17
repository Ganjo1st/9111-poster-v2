#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Управление браузером для публикации
Исправленная проверка авторизации (поиск ID на странице)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import os
from typing import Optional

logger = logging.getLogger('browser_manager')

class BrowserManager:
    """Управляет браузером для публикации на 9111.ru"""

    def __init__(self, email: str, password: str, user_id: str, headless: bool = False):
        self.email = email
        self.password = password
        self.user_id = user_id
        self.user_hash = '791c6e0d36d492ce0a5d8fcb656c1111'  # Ваш хеш из логов
        self.headless = headless
        self.driver = None
        self.wait = None

    def start(self) -> bool:
        """Запускает браузер"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument("--headless=new")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            # Скрываем автоматизацию
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ Браузер запущен")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка запуска браузера: {e}")
            return False

    def stop(self):
        """Останавливает браузер"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🛑 Браузер закрыт")
            except:
                pass

    def save_screenshot(self, name: str = None):
        """Сохраняет скриншот"""
        if not self.driver:
            return

        if not name:
            name = f"screenshots/screenshot_{int(time.time())}.png"

        try:
            self.driver.save_screenshot(name)
            logger.info(f"📸 Скриншот: {name}")
        except:
            pass

    def check_authorization(self) -> bool:
        """
        Проверяет авторизацию по наличию ID пользователя и других признаков на странице.
        НЕ ИСПОЛЬЗУЕТ ПРОВЕРКУ ПО URL!
        """
        try:
            # Получаем HTML страницы
            page_source = self.driver.page_source

            # 1. Проверяем наличие ВАШЕГО user_hash (самый надежный способ)
            if self.user_hash in page_source:
                logger.info("✅ Найден user_hash - авторизация подтверждена")
                return True

            # 2. Проверяем наличие ВАШЕГО ID
            if self.user_id in page_source:
                logger.info(f"✅ Найден ID пользователя {self.user_id} - авторизация подтверждена")
                return True

            # 3. Проверяем элементы, которые видны только авторизованным
            auth_indicators = [
                'Выход',
                'Мои публикации',
                'Баланс',
                'Профиль',
                'notification-bell',
                'userMenuOpen'
            ]

            for indicator in auth_indicators:
                if indicator in page_source:
                    logger.info(f"✅ Найден индикатор авторизации: '{indicator}'")
                    return True

            # 4. Проверяем, не на странице ли входа мы случайно
            login_indicators = ['Вход', 'Пароль', 'Войти по паролю', 'Забыли пароль?']
            login_page_score = sum(1 for ind in login_indicators if ind in page_source)

            if login_page_score >= 3:
                logger.warning("⚠️ Обнаружена страница входа, авторизации нет")
                return False

            # Если ничего не нашли
            logger.warning("⚠️ Признаки авторизации не найдены")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка проверки авторизации: {e}")
            return False

    def login(self) -> bool:
        """Выполняет вход на сайт"""
        try:
            logger.info("🔑 Выполняем вход...")

            # Открываем страницу входа
            self.driver.get("https://9111.ru/login/")
            time.sleep(3)

            self.save_screenshot('login_page.png')

            # Вводим email
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.clear()
            email_input.send_keys(self.email)
            logger.info("✅ Email введен")
            time.sleep(1)

            # Нажимаем "Войти по паролю" (если нужно)
            try:
                password_btn = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Войти по паролю')]")
                password_btn.click()
                logger.info("✅ Нажата кнопка 'Войти по паролю'")
                time.sleep(2)
            except:
                logger.info("ℹ️ Кнопка 'Войти по паролю' не понадобилась")

            # Вводим пароль
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("✅ Пароль введен")
            time.sleep(1)

            # Нажимаем кнопку входа
            submit_btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
            submit_btn.click()
            logger.info("✅ Кнопка входа нажата")

            # Ждем загрузки
            time.sleep(5)

            # ВАЖНО: Проверяем авторизацию по содержимому страницы, а не по URL!
            logger.info(f"📍 Текущий URL после входа: {self.driver.current_url}")

            if self.check_authorization():
                logger.info("🎉 Вход выполнен успешно!")
                self.save_screenshot('after_login.png')
                return True
            else:
                logger.error("❌ Не удалось подтвердить вход (ID пользователя не найден на странице)")
                self.save_screenshot('login_failed.png')
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            self.save_screenshot('login_error.png')
            return False

    def publish_post(self, title: str, content: str, photo_path: str = None) -> bool:
        """Публикует пост с возможностью прикрепить фото"""
        try:
            logger.info(f"📝 Публикуем: {title[:50]}...")

            actions = ActionChains(self.driver)

            # Открываем страницу публикации
            self.driver.get("https://9111.ru/pubs/add/title/")
            time.sleep(5)

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

            # Загружаем фото если есть
            if photo_path and os.path.exists(photo_path):
                try:
                    # Нажимаем кнопку "+ Фото"
                    photo_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '+ Фото')]")
                    actions.move_to_element(photo_btn).perform()
                    photo_btn.click()
                    logger.info("✅ Нажата кнопка '+ Фото'")
                    time.sleep(2)

                    # Ищем input для загрузки файла
                    file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                    file_input.send_keys(os.path.abspath(photo_path))
                    logger.info(f"✅ Фото загружено: {photo_path}")
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось загрузить фото: {e}")

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
                tags.send_keys("новости, события")
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
            self.save_screenshot('publish_error.png')
            return False
