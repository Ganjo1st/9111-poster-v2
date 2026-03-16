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
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("Браузер запущен")
        return True
    
    def stop(self):
        if self.driver:
            self.driver.quit()
    
    def save_screenshot(self, name):
        self.driver.save_screenshot(name)
    
    def login(self):
        logger.info("Вход на сайт...")
        self.driver.get("https://9111.ru/login/")
        time.sleep(3)
        self.save_screenshot("1_login_page.png")
        
        email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(self.email)
        
        password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(self.password)
        
        submit = self.driver.find_element(By.XPATH, "//input[@type='submit']")
        submit.click()
        time.sleep(5)
        
        if self.user_id in self.driver.page_source:
            logger.info("Вход успешен")
            self.save_screenshot("2_after_login.png")
            return True
        logger.error("Вход не удался")
        return False
