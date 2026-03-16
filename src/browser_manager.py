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
        """Запуск браузера с правильными настройками"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Важные аргументы для стабильной работы
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
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
    
    def check_authorization(self) -> bool:
        """Проверка авторизации ТОЛЬКО по содержимому страницы, НЕ ПО URL!"""
        try:
            page_source = self.driver.page_source
            
            # Проверяем наличие ID пользователя на странице
            if self.user_id in page_source:
                logger.info(f"✅ Найден ID пользователя {self.user_id} - авторизация подтверждена")
                return True
            
            # Проверяем признаки авторизации
            auth_indicators = ['Выход', 'Мои публикации', 'Баланс', 'Профиль']
            for indicator in auth_indicators:
                if indicator in page_source:
                    logger.info(f"✅ Найден индикатор: '{indicator}'")
                    return True
            
            logger.warning("⚠️ Признаки авторизации не найдены")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки авторизации: {e}")
            return False
    
    def login(self) -> bool:
        """Вход на сайт с правильной проверкой"""
        try:
            logger.info("🔑 Вход на сайт...")
            
            # Сначала переходим на главную
            self.driver.get("https://9111.ru/")
            time.sleep(3)
            self.save_screenshot("1_main_page.png")
            
            # Ищем и кликаем по кнопке "Вход"
            try:
                login_link = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Вход')]")
                login_link.click()
                time.sleep(3)
            except:
                # Если не нашли, пробуем прямой переход
                self.driver.get("https://9111.ru/login/")
                time.sleep(3)
            
            self.save_screenshot("2_login_page.png")
            
            # Ждем поле email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            logger.info("✅ Email введен")
            
            # Ждем поле пароля
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("✅ Пароль введен")
            
            # Нажимаем кнопку входа
            submit = self.driver.find_element(By.XPATH, "//input[@type='submit']")
            submit.click()
            logger.info("✅ Кнопка входа нажата")
            
            # Ждем загрузки
            time.sleep(5)
            self.save_screenshot("3_after_login.png")
            
            # ВАЖНО: Проверяем авторизацию по содержимому, НЕ ПО URL!
            if self.check_authorization():
                logger.info("🎉 Вход выполнен успешно!")
                return True
            else:
                logger.error("❌ Не удалось подтвердить вход")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            self.save_screenshot("error.png")
            return False
