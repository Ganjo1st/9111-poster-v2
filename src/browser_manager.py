import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class BrowserManager:
    """Управление браузером и авторизацией на 9111.ru"""
    
    def __init__(self):
        self.login_url = "https://9111.ru/"
        self.email = os.getenv('NINTH_EMAIL')
        self.password = os.getenv('NINTH_PASSWORD')
        self.user_hash = os.getenv('USER_HASH')
        self.ukk = os.getenv('UKK')
        
        if not all([self.email, self.password]):
            logger.error("❌ Не заданы EMAIL или PASSWORD в переменных окружения")
            
    def init_browser(self, headless=True):
        """Инициализация браузера с настройками"""
        logger.info("🔧 Настройка Chrome...")
        
        chrome_options = Options()
        
        if headless:
            logger.info("🌐 Режим headless (без графического интерфейса)")
            chrome_options.add_argument("--headless=new")
        
        # Важные аргументы для работы в GitHub Actions
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Дополнительные аргументы для стабильности
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            logger.info("🚀 Запуск Chrome...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("✅ Браузер успешно запущен")
            return driver
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске браузера: {e}")
            return None
            
    def login(self, driver):
        """Авторизация на сайте 9111.ru"""
        logger.info("🔐 Попытка авторизации...")
        
        try:
            # Переходим на главную
            logger.info(f"🌐 Открываем {self.login_url}")
            driver.get(self.login_url)
            time.sleep(3)
            
            # Ищем кнопку входа
            logger.info("🔍 Поиск кнопки входа...")
            login_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Вход') or contains(text(), 'войти')]")
            
            if login_buttons:
                logger.info(f"✅ Найдена кнопка входа, кликаем")
                login_buttons[0].click()
                time.sleep(2)
            
            # Вводим email
            logger.info("📧 Ввод email...")
            email_input = driver.find_element(By.NAME, "login")
            email_input.clear()
            email_input.send_keys(self.email)
            
            # Вводим пароль
            logger.info("🔑 Ввод пароля...")
            password_input = driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Нажимаем кнопку входа
            logger.info("🚀 Нажатие кнопки входа...")
            submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")
            if submit_buttons:
                submit_buttons[0].click()
            
            time.sleep(5)
            
            # Проверяем успешность входа
            if "Вход" not in driver.page_source and "войти" not in driver.page_source.lower():
                logger.info("✅ Похоже, авторизация успешна")
                return True
            else:
                logger.error("❌ Возможно, авторизация не удалась")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при авторизации: {e}")
            return False
