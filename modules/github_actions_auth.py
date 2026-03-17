import os
import logging
import pickle
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from modules.exceptions import AuthError
from modules.logger import log_function_call

logger = logging.getLogger(__name__)


class GitHubActionsAuth:
    """
    Авторизация для GitHub Actions с использованием кук и прямых параметров.
    Использует Selenium с headless Chrome.
    """
    
    def __init__(self, email: str, password: str, user_hash: str = None, uuk: str = None):
        self.email = email
        self.password = password
        self.user_hash = user_hash
        self.uuk = uuk
        self.driver = None
        self.cookies_file = Path("sessions/cookies.pkl")
        
    def _create_driver(self):
        """Создание headless Chrome драйвера для GitHub Actions."""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Добавляем экспериментальные опции для обхода детекта ботов
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Исполняем JS для маскировки webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    @log_function_call
    def login_with_cookies(self) -> bool:
        """
        Пытается войти используя сохраненные куки.
        """
        if not self.cookies_file.exists():
            logger.info("Файл с куками не найден")
            return False
            
        try:
            self._create_driver()
            self.driver.get("https://9111.ru")
            time.sleep(3)
            
            with open(self.cookies_file, "rb") as f:
                cookies = pickle.load(f)
                
            for cookie in cookies:
                # Обрабатываем куки для Selenium
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Не удалось добавить куку {cookie.get('name')}: {e}")
                    
            self.driver.refresh()
            time.sleep(3)
            
            # Проверяем, что мы авторизованы
            if self._check_login_status():
                logger.info("✅ Успешный вход по кукам")
                return True
            else:
                logger.warning("Куки недействительны")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при входе по кукам: {e}")
            return False
    
    @log_function_call
    def login_with_credentials(self) -> bool:
        """
        Вход с использованием email и пароля.
        """
        try:
            if not self.driver:
                self._create_driver()
                
            logger.info("Переход на страницу входа...")
            self.driver.get("https://9111.ru")
            time.sleep(3)
            
            # Ищем форму входа
            login_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Вход') or contains(text(), 'Войти')]"))
            )
            login_link.click()
            time.sleep(2)
            
            # Заполняем форму
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.send_keys(self.email)
            
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            
            # Отправляем форму
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            time.sleep(5)
            
            # Проверяем успешность входа
            if self._check_login_status():
                logger.info("✅ Успешный вход по логину/паролю")
                self._save_cookies()
                return True
            else:
                logger.error("❌ Не удалось войти")
                return False
                
        except Exception as e:
            logger.exception(f"Ошибка при входе: {e}")
            return False
    
    def _check_login_status(self) -> bool:
        """
        Проверяет, авторизован ли пользователь.
        """
        try:
            # Проверяем наличие элементов, характерных для авторизованного пользователя
            # Например, наличие элемента с классом userMenuOpen или ссылки на профиль
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "userMenuOpen"))
            )
            return True
        except:
            try:
                # Альтернативная проверка
                current_url = self.driver.current_url
                if "/my/" in current_url or "/user-" in current_url:
                    return True
            except:
                pass
            return False
    
    def _save_cookies(self):
        """Сохраняет куки для последующего использования."""
        if self.driver:
            cookies = self.driver.get_cookies()
            self.cookies_file.parent.mkdir(exist_ok=True)
            with open(self.cookies_file, "wb") as f:
                pickle.dump(cookies, f)
            logger.info(f"Сохранено {len(cookies)} кук")
    
    def ensure_login(self) -> bool:
        """
        Гарантирует, что мы авторизованы. Сначала пробует куки, затем логин/пароль.
        """
        # Пробуем войти по кукам
        if self.login_with_cookies():
            return True
            
        # Если не получилось, пробуем логин/пароль
        logger.info("Пробуем войти с логином/паролем...")
        return self.login_with_credentials()
    
    def get_driver(self):
        """Возвращает драйвер с авторизованной сессией."""
        return self.driver
    
    def close(self):
        """Закрывает драйвер."""
        if self.driver:
            self.driver.quit()
