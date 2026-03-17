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
    
    def debug_page_info(self, stage):
        """Собирает отладочную информацию о странице"""
        try:
            logger.info(f"=== ДЕБАГ {stage} ===")
            logger.info(f"URL: {self.driver.current_url}")
            logger.info(f"Title: {self.driver.title}")
            
            # Сохраняем HTML для анализа (первые 1000 символов)
            html = self.driver.page_source[:1000]
            logger.info(f"HTML preview: {html[:500]}")
            
            # Проверяем наличие ключевых слов
            page_text = self.driver.page_source.lower()
            keywords = {
                'email': 'email' in page_text,
                'password': 'password' in page_text,
                'login': 'login' in page_text or 'вход' in page_text,
                'register': 'register' in page_text or 'регистрация' in page_text
            }
            logger.info(f"Keywords found: {keywords}")
            
            return keywords
        except Exception as e:
            logger.error(f"Ошибка дебага: {e}")
            return {}
    
    def find_input_fields(self):
        """Ищет все возможные поля ввода на странице"""
        try:
            # Ищем все input поля
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Найдено input полей: {len(inputs)}")
            
            for i, inp in enumerate(inputs):
                try:
                    inp_type = inp.get_attribute("type")
                    inp_name = inp.get_attribute("name")
                    inp_id = inp.get_attribute("id")
                    inp_placeholder = inp.get_attribute("placeholder")
                    inp_class = inp.get_attribute("class")
                    
                    logger.info(f"Input {i}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}, class={inp_class}")
                except:
                    pass
            
            return inputs
        except Exception as e:
            logger.error(f"Ошибка поиска полей: {e}")
            return []
    
    def check_authorization(self) -> bool:
        """Проверка авторизации ТОЛЬКО по содержимому страницы"""
        try:
            page_source = self.driver.page_source
            logger.info(f"Проверка авторизации: ищем ID {self.user_id}")
            
            if self.user_id in page_source:
                logger.info(f"✅ Найден ID пользователя {self.user_id}")
                return True
            
            auth_indicators = ['Выход', 'Мои публикации', 'Баланс', 'Профиль']
            for indicator in auth_indicators:
                if indicator in page_source:
                    logger.info(f"✅ Найден индикатор: '{indicator}'")
                    return True
            
            logger.warning("❌ Признаки авторизации не найдены")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки авторизации: {e}")
            return False
    
    def login(self) -> bool:
        """Улучшенный вход с детальным логированием"""
        try:
            logger.info("🔑 Начинаем процесс входа...")
            
            # ШАГ 1: Переход на главную
            logger.info("Переходим на главную страницу...")
            self.driver.get("https://9111.ru/")
            time.sleep(3)
            self.save_screenshot("1_main_page.png")
            self.debug_page_info("MAIN_PAGE")
            
            # ШАГ 2: Поиск ссылки на вход
            logger.info("Ищем ссылку на вход...")
            login_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Вход') or contains(text(), 'вход') or contains(@href, 'login')]")
            logger.info(f"Найдено ссылок на вход: {len(login_links)}")
            
            if login_links:
                login_links[0].click()
                logger.info("Клик по ссылке входа")
                time.sleep(3)
            else:
                logger.warning("Ссылка на вход не найдена, пробуем прямой переход")
                self.driver.get("https://9111.ru/login/")
                time.sleep(3)
            
            self.save_screenshot("2_login_page.png")
            self.debug_page_info("LOGIN_PAGE")
            
            # ШАГ 3: Анализ полей ввода
            logger.info("Анализируем поля ввода на странице...")
            inputs = self.find_input_fields()
            
            if len(inputs) < 2:
                logger.error("Недостаточно полей ввода на странице!")
                return False
            
            # ШАГ 4: Пробуем найти поле email
            email_field = None
            password_field = None
            
            # Пробуем разные селекторы для email
            email_selectors = [
                (By.NAME, "email"),
                (By.NAME, "login"),
                (By.NAME, "username"),
                (By.ID, "email"),
                (By.ID, "login"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.XPATH, "//input[@placeholder='Email' or contains(@placeholder, 'email')]"),
                (By.XPATH, "//input[@placeholder='Логин' or contains(@placeholder, 'логин')]"),
                (By.XPATH, "//input[@placeholder='Телефон' or contains(@placeholder, 'телефон')]")
            ]
            
            for selector_type, selector_value in email_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        email_field = elements[0]
                        logger.info(f"✅ Нашли поле email по селектору: {selector_type}={selector_value}")
                        break
                except:
                    continue
            
            # Пробуем найти поле пароля
            password_selectors = [
                (By.NAME, "password"),
                (By.NAME, "pass"),
                (By.ID, "password"),
                (By.ID, "pass"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        password_field = elements[0]
                        logger.info(f"✅ Нашли поле пароля по селектору: {selector_type}={selector_value}")
                        break
                except:
                    continue
            
            if not email_field or not password_field:
                logger.error("❌ Не удалось найти поля для ввода!")
                logger.error(f"Email field found: {bool(email_field)}")
                logger.error(f"Password field found: {bool(password_field)}")
                return False
            
            # ШАГ 5: Ввод данных
            email_field.clear()
            email_field.send_keys(self.email)
            logger.info("✅ Email введен")
            
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("✅ Пароль введен")
            
            # ШАГ 6: Поиск кнопки отправки
            logger.info("Ищем кнопку отправки...")
            submit_buttons = self.driver.find_elements(By.XPATH, 
                "//input[@type='submit'] | //button[@type='submit'] | //button[contains(text(), 'Войти')] | //button[contains(text(), 'Вход')]")
            
            if not submit_buttons:
                logger.error("❌ Не найдена кнопка отправки!")
                return False
            
            logger.info(f"Найдено кнопок: {len(submit_buttons)}")
            submit_buttons[0].click()
            logger.info("✅ Кнопка входа нажата")
            
            # ШАГ 7: Ожидание результата
            time.sleep(5)
            self.save_screenshot("3_after_login.png")
            self.debug_page_info("AFTER_LOGIN")
            
            # ШАГ 8: Проверка авторизации
            if self.check_authorization():
                logger.info("🎉 ВХОД ВЫПОЛНЕН УСПЕШНО!")
                return True
            else:
                # Проверяем, не появилась ли ошибка на странице
                page_text = self.driver.page_source.lower()
                error_indicators = ['ошибк', 'error', 'неверн', 'invalid', 'неправильн']
                for error in error_indicators:
                    if error in page_text:
                        logger.error(f"❌ Обнаружено сообщение об ошибке: '{error}'")
                        break
                
                logger.error("❌ Не удалось подтвердить вход")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            self.save_screenshot("error.png")
            return False
