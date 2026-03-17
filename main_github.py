import requests
import os
import logging
import socket
from urllib.parse import urlparse

def test_proxy(proxy_string):
    """
    Тестирование прокси из Python
    """
    try:
        proxies = {
            'http': f'http://{proxy_string}',
            'https': f'http://{proxy_string}'
        }
        
        # Тест 1: HTTP
        response = requests.get(
            'http://httpbin.org/get',
            proxies=proxies,
            timeout=10
        )
        if response.status_code != 200:
            logging.error(f"❌ HTTP тест провален: {response.status_code}")
            return False
            
        # Тест 2: HTTPS
        response = requests.get(
            'https://httpbin.org/get',
            proxies=proxies,
            timeout=10
        )
        if response.status_code != 200:
            logging.error(f"❌ HTTPS тест провален: {response.status_code}")
            return False
            
        # Тест 3: Google (для Chrome)
        response = requests.get(
            'https://www.google.com',
            proxies=proxies,
            timeout=10
        )
        if response.status_code != 200:
            logging.error(f"❌ Google тест провален: {response.status_code}")
            return False
            
        # Тест 4: Chrome API
        response = requests.get(
            'https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json',
            proxies=proxies,
            timeout=15
        )
        if response.status_code != 200:
            logging.error(f"❌ Chrome API тест провален: {response.status_code}")
            return False
            
        logging.info(f"✅ Все тесты прокси пройдены успешно")
        return True
        
    except requests.exceptions.ConnectTimeout:
        logging.error("❌ Таймаут подключения к прокси")
        return False
    except requests.exceptions.ProxyError as e:
        logging.error(f"❌ Ошибка прокси: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Неожиданная ошибка при тестировании прокси: {e}")
        return False

def setup_driver():
    """
    Настройка драйвера с проверкой прокси
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Настройка прокси если есть
    proxy = os.environ.get('PROXY')
    use_proxy = os.environ.get('USE_PROXY', 'false').lower() == 'true'
    
    if proxy and use_proxy:
        logging.info(f"🔌 Настраиваем прокси: {proxy}")
        
        # Проверяем прокси перед использованием
        if test_proxy(proxy):
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
            # Исключаем локальные адреса из прокси
            chrome_options.add_argument('--proxy-bypass-list=localhost;127.0.0.1;')
        else:
            logging.warning("⚠️ Прокси не прошел тесты, запускаем без прокси")
            os.environ['USE_PROXY'] = 'false'
    
    try:
        # Устанавливаем таймауты для ChromeDriver
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'performance': 'ALL', 'browser': 'ALL'}
        
        service = Service('/usr/bin/chromedriver') if os.path.exists('/usr/bin/chromedriver') else Service()
        
        driver = webdriver.Chrome(
            options=chrome_options,
            service=service,
            desired_capabilities=capabilities
        )
        
        # Устанавливаем таймауты
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        
        logging.info("✅ Драйвер успешно инициализирован")
        return driver
        
    except Exception as e:
        logging.error(f"❌ Ошибка при инициализации драйвера: {e}")
        
        # Если ошибка с прокси, пробуем без него
        if 'proxy' in str(e).lower() and use_proxy:
            logging.info("🔄 Пробуем без прокси...")
            chrome_options.add_argument('--proxy-server="direct://"')
            chrome_options.add_argument('--proxy-bypass-list=*')
            try:
                driver = webdriver.Chrome(options=chrome_options)
                logging.info("✅ Драйвер успешно инициализирован без прокси")
                return driver
            except Exception as e2:
                logging.error(f"❌ Ошибка даже без прокси: {e2}")
                raise
        else:
            raise

def main():
    """
    Основная функция
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/poster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('9111_poster')
    
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster")
    logger.info("=" * 50)
    
    # Проверяем настройки прокси
    proxy = os.environ.get('PROXY')
    use_proxy = os.environ.get('USE_PROXY', 'false').lower() == 'true'
    
    if proxy and use_proxy:
        logger.info(f"🔌 Используем прокси: {proxy}")
    else:
        logger.info("🔌 Работаем без прокси")
    
    # Продолжаем основную логику...
    try:
        driver = setup_driver()
        # ... остальной код
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
