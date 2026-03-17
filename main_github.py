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
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--lang=ru-RU")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def add_cookies_from_file(driver, target_url):
    """Добавляет куки после перехода на целевой URL"""
    cookies = [
        {'name': 'user_hash', 'value': Config.USER_HASH, 'domain': '.9111.ru', 'path': '/'},
        {'name': 'uuk', 'value': 'cad1a52ec9d948e6cc9ef7cae9009203', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'geo', 'value': '91-817-1', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'au', 'value': '%7B%22u%22%3A2368040%2C%22k%22%3A%22aa8ca3729252da5450cdb0862352503d%22%2C%22t%22%3A1773747508%7D', 'domain': '.9111.ru', 'path': '/'},
    ]
    
    # Переходим на целевой URL
    logger.info("=" * 50)
    logger.info(f"🌐 Переходим на {target_url}")
    driver.get(target_url)
    time.sleep(5)
    
    # Сохраняем скриншот до добавления кук
    driver.save_screenshot("before_cookies.png")
    logger.info("📸 Скриншот до добавления кук: before_cookies.png")
    
    # Добавляем куки
    logger.info("=" * 50)
    logger.info("🍪 Добавляем куки...")
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
            logger.info(f"✅ Добавлена кука: {cookie['name']}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось добавить куку {cookie['name']}: {e}")
    
    # Обновляем страницу
    logger.info("=" * 50)
    logger.info("🔄 Обновляем страницу...")
    driver.refresh()
    time.sleep(5)
    
    # Сохраняем скриншот после добавления кук
    driver.save_screenshot("after_cookies.png")
    logger.info("📸 Скриншот после добавления кук: after_cookies.png")
    
    # Проверяем результат
    current_url = driver.current_url
    page_title = driver.title
    logger.info(f"📍 Текущий URL: {current_url}")
    logger.info(f"📄 Заголовок страницы: {page_title}")
    
    # Проверяем наличие формы (признак успеха)
    try:
        form = driver.find_element(By.ID, "form_create_topic_group")
        logger.info("✅ ФОРМА НАЙДЕНА! Авторизация успешна")
        return True
    except:
        logger.error("❌ Форма не найдена")
        # Сохраняем HTML для анализа
        with open("error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("📄 HTML страницы сохранен: error_page.html")
        return False


def create_publication(driver, title: str, content: str, rubric_name: str = "новости", tags: str = ""):
    """Создает публикацию через Selenium"""
    timestamp = int(time.time())
    
    try:
        # Проверяем наличие формы
        try:
            form = driver.find_element(By.ID, "form_create_topic_group")
            logger.info("✅ Форма найдена, начинаем заполнение")
        except:
            logger.error("❌ Форма не найдена перед заполнением")
            return False
        
        # Вводим заголовок
        logger.info("➡️ Вводим заголовок...")
        title_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "topic_name"))
        )
        title_div.click()
        title_div.clear()
        title_div.send_keys(title)
        logger.info(f"   ✅ Заголовок: {title}")
        time.sleep(2)
        
        # Выбираем рубрику
        logger.info("➡️ Выбираем рубрику...")
        rubric_select = driver.find_element(By.ID, "rubric_id2")
        rubric_id = get_rubric_id(rubric_name)
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))",
            rubric_select,
            str(rubric_id)
        )
        logger.info(f"   ✅ Рубрика: {rubric_name} (ID: {rubric_id})")
        time.sleep(2)
        
        # Вводим текст
        logger.info("➡️ Вводим текст...")
        editor = driver.find_element(By.ID, "lite_editor")
        editor.click()
        editor.send_keys(content)
        logger.info(f"   ✅ Текст (длина: {len(content)})")
        time.sleep(2)
        
        # Вводим теги
        if tags:
            try:
                tags_input = driver.find_element(By.ID, "tag_list_input")
                tags_input.clear()
                tags_input.send_keys(tags)
                logger.info(f"   ✅ Теги: {tags}")
                time.sleep(2)
            except:
                logger.warning("   ⚠️ Теги не введены")
        
        # Сохраняем скриншот перед отправкой
        driver.save_screenshot(f"before_submit_{timestamp}.png")
        
        # Отправляем форму
        logger.info("➡️ Отправляем форму...")
        submit_btn = driver.find_element(By.ID, "button_create_pubs")
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
        time.sleep(1)
        submit_btn.click()
        time.sleep(5)
        
        # Проверяем результат
        page_source = driver.page_source.lower()
        driver.save_screenshot(f"result_{timestamp}.png")
        
        if "спасибо" in page_source or "публикация успешно" in page_source:
            logger.info("✅ Публикация успешна!")
            return True
        elif "уникален" in page_source:
            logger.warning("⚠️ Заголовок не уникален")
            return False
        else:
            logger.error("❌ Неизвестный результат")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        driver.save_screenshot(f"error_{timestamp}.png")
        return False


def get_telegram_posts():
    """Получает посты из Telegram"""
    logger.info("🤖 Получаем посты из Telegram...")
    
    parser = TelegramBotParser(Config.TELEGRAM_TOKEN, Config.CHANNEL_ID)
    
    try:
        raw_posts = parser.parse_channel_posts()
        
        if raw_posts:
            logger.info(f"📦 Получено {len(raw_posts)} сырых постов")
            
            posts = []
            for raw in raw_posts:
                if isinstance(raw, dict):
                    post = {
                        'title': raw.get('text', '')[:100],
                        'content': raw.get('text', ''),
                    }
                    if post['content']:
                        posts.append(post)
                        logger.info(f"  Пост: {post['title'][:30]}...")
            
            logger.info(f"✅ Преобразовано {len(posts)} постов")
            return posts
        
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
    
    return []


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster (Прямая авторизация)")
    logger.info("=" * 50)

    # 1. Настраиваем драйвер
    driver = setup_driver()
    
    try:
        # 2. Сразу переходим на страницу создания и добавляем куки
        target_url = "https://9111.ru/pubs/add/title/"
        if not add_cookies_from_file(driver, target_url):
            logger.error("❌ Не удалось получить доступ к странице создания")
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
            logger.info("=" * 50)
            logger.info(f"📝 Пост {i}/{len(posts)}")
            logger.info("=" * 50)
            
            title = post.get("title", "").strip()
            content = post.get("content", "").strip()
            
            if not content:
                logger.warning(f"⚠️ Пост {i} пустой")
                continue
            
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
            
            time.sleep(5)
        
        logger.info("=" * 50)
        logger.info(f"📊 ИТОГ: {successful}/{len(posts)}")
        logger.info("=" * 50)
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
