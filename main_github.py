import os
import sys
import time
import pickle
import random
import string
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from modules.config import Config
from modules.logger import setup_logging
from modules.telegram_bot_parser import TelegramBotParser
from modules.rubric_mapper import get_rubric_id

logger = setup_logging()


def make_title_unique(title: str) -> str:
    """Делает заголовок уникальным на 70%"""
    # Добавляем случайное число в конец
    return f"{title} {random.randint(1000, 9999)}"


def setup_driver():
    """Настраивает Chrome driver для headless режима"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # Добавляем аргументы для обхода блокировок
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def login_with_cookies(driver):
    """Загружает сохраненные куки"""
    cookies_file = "sessions/cookies.pkl"
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            driver.get("https://9111.ru")
            time.sleep(2)
            
            for cookie in cookies:
                driver.add_cookie(cookie)
            
            driver.refresh()
            time.sleep(3)
            logger.info("✅ Куки загружены")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кук: {e}")
    return False


def save_cookies(driver):
    """Сохраняет куки после входа"""
    try:
        os.makedirs("sessions", exist_ok=True)
        cookies = driver.get_cookies()
        with open("sessions/cookies.pkl", 'wb') as f:
            pickle.dump(cookies, f)
        logger.info("✅ Куки сохранены")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения кук: {e}")


def login_manually(driver):
    """Ручной вход через форму"""
    try:
        driver.get("https://9111.ru")
        time.sleep(3)
        
        # Ищем кнопку входа
        try:
            login_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Вход')]")
            login_btn.click()
            time.sleep(2)
        except:
            pass
        
        # Вводим логин и пароль
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.send_keys(Config.NINTH_EMAIL)
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(Config.NINTH_PASSWORD)
        
        # Отправляем форму
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        
        time.sleep(5)
        
        # Проверяем успешность входа
        if "user_hash" in driver.page_source:
            logger.info("✅ Вход выполнен успешно")
            save_cookies(driver)
            return True
        else:
            logger.error("❌ Ошибка входа")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при входе: {e}")
        return False


def create_publication(driver, title: str, content: str, rubric_name: str = "новости", tags: str = ""):
    """Создает публикацию через Selenium"""
    try:
        # 1. Переходим на страницу создания
        logger.info("Переходим на страницу создания...")
        driver.get("https://9111.ru/pubs/add/")
        time.sleep(3)
        
        # 2. Выбираем категорию "Новость, статья"
        try:
            news_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Новость, статья')]"))
            )
            news_link.click()
            time.sleep(3)
        except:
            # Возможно уже на странице создания
            driver.get("https://9111.ru/pubs/add/title/")
            time.sleep(3)
        
        # 3. Вводим заголовок
        title_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "topic_name"))
        )
        title_div.click()
        title_div.send_keys(title)
        time.sleep(1)
        
        # 4. Выбираем рубрику
        rubric_select = driver.find_element(By.ID, "rubric_id2")
        rubric_id = get_rubric_id(rubric_name)
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))",
            rubric_select,
            str(rubric_id)
        )
        time.sleep(1)
        
        # 5. Вводим текст
        editor = driver.find_element(By.ID, "lite_editor")
        editor.click()
        editor.send_keys(content)
        time.sleep(1)
        
        # 6. Вводим теги
        tags_input = driver.find_element(By.ID, "tag_list_input")
        tags_input.send_keys(tags)
        time.sleep(1)
        
        # 7. Отправляем форму
        submit_btn = driver.find_element(By.ID, "button_create_pubs")
        submit_btn.click()
        
        # 8. Ждем результат
        time.sleep(5)
        
        # Проверяем успех
        if "спасибо" in driver.page_source.lower() or "публикация успешно" in driver.page_source.lower():
            logger.info("✅ Публикация успешно создана!")
            return True
        else:
            # Проверяем на ошибку уникальности
            if "уникален" in driver.page_source.lower():
                logger.warning("⚠️ Заголовок не уникален")
            else:
                logger.error("❌ Неизвестная ошибка")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при создании публикации: {e}")
        # Делаем скриншот для отладки
        driver.save_screenshot(f"error_{int(time.time())}.png")
        return False


def get_telegram_posts():
    """Получает посты из Telegram"""
    logger.info("🤖 Получаем посты из Telegram...")
    
    parser = TelegramBotParser(Config.TELEGRAM_TOKEN, Config.CHANNEL_ID)
    
    try:
        raw_posts = parser.parse_channel_posts()
        
        if raw_posts:
            logger.info(f"📦 Получено {len(raw_posts)} постов")
            
            posts = []
            for raw in raw_posts:
                if isinstance(raw, dict):
                    post = {
                        'title': raw.get('text', '')[:100],
                        'content': raw.get('text', ''),
                    }
                    if post['content']:
                        posts.append(post)
            
            logger.info(f"✅ Преобразовано {len(posts)} постов")
            return posts
        
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
    
    return []


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster (Selenium)")
    logger.info("=" * 50)

    # 1. Настраиваем драйвер
    driver = setup_driver()
    
    try:
        # 2. Пытаемся загрузить сохраненные куки
        if not login_with_cookies(driver):
            # Если нет кук, входим вручную
            if not login_manually(driver):
                logger.error("❌ Не удалось авторизоваться")
                return
        
        # 3. Получаем посты
        posts = get_telegram_posts()
        if not posts:
            logger.warning("❌ Нет постов")
            return
        
        logger.info(f"✅ Получено {len(posts)} постов")
        
        # 4. Публикуем каждый пост
        successful = 0
        for i, post in enumerate(posts, 1):
            logger.info(f"--- 📝 Пост {i}/{len(posts)} ---")
            
            title = post.get("title", "").strip()
            content = post.get("content", "").strip()
            
            if not content:
                logger.warning(f"⚠️ Пост {i} пустой")
                continue
            
            # Делаем заголовок уникальным
            unique_title = make_title_unique(title)
            logger.info(f"Заголовок: {unique_title}")
            
            success = create_publication(
                driver,
                title=unique_title,
                content=content,
                rubric_name=Config.DEFAULT_RUBRIC,
                tags=Config.DEFAULT_TAGS
            )
            
            if success:
                successful += 1
                logger.info(f"✅ Пост {i} опубликован")
            else:
                logger.error(f"❌ Ошибка поста {i}")
            
            # Небольшая пауза между постами
            time.sleep(5)
        
        logger.info(f"📊 Итог: {successful}/{len(posts)}")
        logger.info("=" * 50)
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
