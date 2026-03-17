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
    
    # Добавляем заголовки как в браузере
    chrome_options.add_argument("--lang=ru-RU")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def check_authorization(driver):
    """Проверяет, авторизован ли пользователь"""
    logger.info("🔍 Проверка авторизации...")
    
    current_url = driver.current_url
    page_title = driver.title
    page_source = driver.page_source
    
    logger.info(f"📍 Текущий URL: {current_url}")
    logger.info(f"📄 Заголовок страницы: {page_title}")
    
    # Проверяем наличие 403 ошибки
    if "403" in page_title or "Forbidden" in page_source:
        logger.error("❌ Обнаружена ошибка 403 Forbidden")
        return False
    
    # Ищем признаки успешной авторизации
    auth_indicators = [
        Config.USER_HASH,
        "user_hash",
        "Мои публикации",
        "Выход",
        "Личный кабинет",
        "Вадим Викторович",  # Имя пользователя из HTML
        "2368040",  # ID пользователя
    ]
    
    # Добавляем часть email если есть
    if Config.NINTH_EMAIL and '@' in Config.NINTH_EMAIL:
        email_part = Config.NINTH_EMAIL.split('@')[0]
        auth_indicators.append(email_part)
    
    for indicator in auth_indicators:
        if indicator and str(indicator) in page_source:
            logger.info(f"✅ Найден признак авторизации: {str(indicator)[:50]}")
            return True
    
    # Проверяем наличие формы входа (признак неавторизованности)
    login_indicators = ["Вход", "Регистрация", "войти", "login"]
    for indicator in login_indicators:
        if indicator.lower() in page_source.lower():
            logger.warning(f"⚠️ Найдена форма входа: '{indicator}'")
            return False
    
    logger.warning("⚠️ Не удалось определить статус авторизации")
    return False


def add_cookies_from_file(driver):
    """Добавляет куки из файла в driver и проверяет авторизацию"""
    cookies = [
        {'name': 'user_hash', 'value': Config.USER_HASH, 'domain': '.9111.ru', 'path': '/'},
        {'name': 'uuk', 'value': 'cad1a52ec9d948e6cc9ef7cae9009203', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'geo', 'value': '91-817-1', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'au', 'value': '%7B%22u%22%3A2368040%2C%22k%22%3A%22aa8ca3729252da5450cdb0862352503d%22%2C%22t%22%3A1773746119%7D', 'domain': '.9111.ru', 'path': '/'},
    ]
    
    # Сначала открываем домен, чтобы можно было добавить куки
    logger.info="=" * 50)
    logger.info("🌐 ШАГ 1: Открываем главную страницу...")
    driver.get("https://9111.ru")
    time.sleep(5)
    
    # Сохраняем скриншот до добавления кук
    driver.save_screenshot("before_cookies.png")
    logger.info("📸 Скриншот до добавления кук: before_cookies.png")
    
    # Проверяем состояние до добавления кук
    logger.info("🔍 Состояние ДО добавления кук:")
    check_authorization(driver)
    
    # Добавляем куки
    logger.info("=" * 50)
    logger.info("🍪 ШАГ 2: Добавляем куки...")
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
            logger.info(f"✅ Добавлена кука: {cookie['name']}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось добавить куку {cookie['name']}: {e}")
    
    # Обновляем страницу
    logger.info("=" * 50)
    logger.info("🔄 ШАГ 3: Обновляем страницу...")
    driver.refresh()
    time.sleep(5)
    
    # Сохраняем скриншот после добавления кук
    driver.save_screenshot("after_cookies.png")
    logger.info("📸 Скриншот после добавления кук: after_cookies.png")
    
    # Проверяем состояние после добавления кук
    logger.info("=" * 50)
    logger.info("🔍 ШАГ 4: Проверка авторизации ПОСЛЕ добавления кук:")
    is_authorized = check_authorization(driver)
    
    # Сохраняем HTML для анализа
    with open("auth_check.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logger.info("📄 HTML страницы сохранен: auth_check.html")
    
    return is_authorized


def create_publication(driver, title: str, content: str, rubric_name: str = "новости", tags: str = ""):
    """Создает публикацию через Selenium с подробной отладкой"""
    timestamp = int(time.time())
    
    try:
        # 1. Переходим на страницу создания
        logger.info("=" * 50)
        logger.info("➡️ ШАГ 1: Переходим на страницу создания...")
        driver.get("https://9111.ru/pubs/add/")
        time.sleep(5)
        logger.info(f"   Текущий URL: {driver.current_url}")
        logger.info(f"   Заголовок страницы: {driver.title}")
        
        # Проверяем на 403
        if "403" in driver.title or "Forbidden" in driver.page_source:
            logger.error("❌ ПОЛУЧЕНА ОШИБКА 403 FORBIDDEN!")
            logger.error("   Возможно, куки устарели или требуется повторная авторизация")
            driver.save_screenshot(f"error_403_{timestamp}.png")
            
            # Проверяем, не перенаправило ли на главную
            if "9111.ru" in driver.current_url and "/pubs/add/" not in driver.current_url:
                logger.info("   ⚠️ Произошло перенаправление на главную страницу")
            return False
        
        # Сохраняем скриншот
        screenshot1 = f"step1_main_{timestamp}.png"
        driver.save_screenshot(screenshot1)
        logger.info(f"   📸 Скриншот сохранен: {screenshot1}")
        
        # 2. Ищем ссылку на создание новости
        logger.info("➡️ ШАГ 2: Ищем ссылку 'Новость, статья'...")
        try:
            # Пробуем найти по разным вариантам текста
            xpath_variants = [
                "//a[contains(text(), 'Новость')]",
                "//a[contains(text(), 'новость')]",
                "//a[contains(text(), 'статья')]",
                "//a[contains(text(), 'Статья')]",
                "//a[contains(@href, 'title')]"
            ]
            
            found = False
            for xpath in xpath_variants:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    logger.info(f"   Найдено {len(elements)} элементов по XPath: {xpath}")
                    elements[0].click()
                    logger.info(f"   ✅ Кликнули по элементу")
                    found = True
                    break
            
            if not found:
                logger.warning("   ⚠️ Ссылка не найдена, переходим напрямую")
                driver.get("https://9111.ru/pubs/add/title/")
            
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка при выборе категории: {e}")
            driver.get("https://9111.ru/pubs/add/title/")
            time.sleep(5)
        
        logger.info(f"   Текущий URL после выбора: {driver.current_url}")
        screenshot2 = f"step2_after_category_{timestamp}.png"
        driver.save_screenshot(screenshot2)
        logger.info(f"   📸 Скриншот сохранен: {screenshot2}")
        
        # 3. Проверяем наличие формы
        logger.info("➡️ ШАГ 3: Проверяем наличие формы...")
        try:
            form = driver.find_element(By.ID, "form_create_topic_group")
            logger.info("   ✅ Форма найдена")
            
            # Сохраняем HTML формы для отладки
            with open(f"form_html_{timestamp}.html", "w", encoding="utf-8") as f:
                f.write(form.get_attribute('outerHTML'))
            logger.info(f"   📄 HTML формы сохранен")
            
        except NoSuchElementException:
            logger.error("   ❌ Форма не найдена!")
            logger.error(f"   Полный HTML страницы сохранен")
            with open(f"page_no_form_{timestamp}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.save_screenshot(f"error_no_form_{timestamp}.png")
            return False
        
        # 4. Вводим заголовок
        logger.info("➡️ ШАГ 4: Вводим заголовок...")
        try:
            title_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "topic_name"))
            )
            title_div.click()
            title_div.clear()
            title_div.send_keys(title)
            logger.info(f"   ✅ Заголовок введен: {title}")
            time.sleep(2)
        except Exception as e:
            logger.error(f"   ❌ Ошибка при вводе заголовка: {e}")
            driver.save_screenshot(f"error_title_{timestamp}.png")
            return False
        
        # 5. Выбираем рубрику
        logger.info("➡️ ШАГ 5: Выбираем рубрику...")
        try:
            rubric_select = driver.find_element(By.ID, "rubric_id2")
            rubric_id = get_rubric_id(rubric_name)
            driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'))",
                rubric_select,
                str(rubric_id)
            )
            logger.info(f"   ✅ Рубрика выбрана: {rubric_name} (ID: {rubric_id})")
            time.sleep(2)
        except Exception as e:
            logger.error(f"   ❌ Ошибка при выборе рубрики: {e}")
            driver.save_screenshot(f"error_rubric_{timestamp}.png")
            return False
        
        # 6. Вводим текст
        logger.info("➡️ ШАГ 6: Вводим текст...")
        try:
            editor = driver.find_element(By.ID, "lite_editor")
            editor.click()
            editor.send_keys(content)
            logger.info(f"   ✅ Текст введен (длина: {len(content)} символов)")
            time.sleep(2)
        except Exception as e:
            logger.error(f"   ❌ Ошибка при вводе текста: {e}")
            driver.save_screenshot(f"error_content_{timestamp}.png")
            return False
        
        # 7. Вводим теги
        logger.info("➡️ ШАГ 7: Вводим теги...")
        try:
            tags_input = driver.find_element(By.ID, "tag_list_input")
            tags_input.clear()
            tags_input.send_keys(tags)
            logger.info(f"   ✅ Теги введены: {tags}")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"   ⚠️ Ошибка при вводе тегов: {e}")
            # Не критично, продолжаем
        
        screenshot_before_submit = f"step_before_submit_{timestamp}.png"
        driver.save_screenshot(screenshot_before_submit)
        logger.info(f"   📸 Скриншот перед отправкой: {screenshot_before_submit}")
        
        # 8. Отправляем форму
        logger.info("➡️ ШАГ 8: Отправляем форму...")
        try:
            submit_btn = driver.find_element(By.ID, "button_create_pubs")
            # Прокручиваем к кнопке
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
            time.sleep(1)
            submit_btn.click()
            logger.info("   ✅ Кнопка нажата")
            time.sleep(5)
        except Exception as e:
            logger.error(f"   ❌ Ошибка при нажатии кнопки: {e}")
            driver.save_screenshot(f"error_submit_{timestamp}.png")
            return False
        
        # 9. Проверяем результат
        logger.info("➡️ ШАГ 9: Проверяем результат...")
        final_url = driver.current_url
        page_source = driver.page_source.lower()
        
        screenshot_final = f"final_result_{timestamp}.png"
        driver.save_screenshot(screenshot_final)
        logger.info(f"   📸 Финальный скриншот: {screenshot_final}")
        logger.info(f"   URL после отправки: {final_url}")
        
        # Сохраняем HTML ответа
        with open(f"response_page_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"   📄 HTML ответа сохранен")
        
        # Проверяем признаки успеха
        if "спасибо" in page_source:
            logger.info("✅ НАЙДЕНО: 'спасибо'")
            return True
        elif "публикация успешно" in page_source:
            logger.info("✅ НАЙДЕНО: 'публикация успешно'")
            return True
        elif "успешно добавлена" in page_source:
            logger.info("✅ НАЙДЕНО: 'успешно добавлена'")
            return True
        elif "опубликована" in page_source:
            logger.info("✅ НАЙДЕНО: 'опубликована'")
            return True
        elif "уникален" in page_source:
            logger.warning("⚠️ НАЙДЕНО: заголовок не уникален")
            return False
        else:
            logger.error("❌ Не найдено признаков успеха или ошибки")
            return False
            
    except Exception as e:
        logger.error(f"❌ Общая ошибка при создании публикации: {e}")
        driver.save_screenshot(f"error_general_{timestamp}.png")
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
    logger.info("🚀 Запуск 9111 Poster (Selenium с подробной отладкой)")
    logger.info("=" * 50)

    # 1. Настраиваем драйвер
    driver = setup_driver()
    
    try:
        # 2. Добавляем куки и проверяем авторизацию
        is_authorized = add_cookies_from_file(driver)
        
        if not is_authorized:
            logger.error("❌ НЕ УДАЛОСЬ АВТОРИЗОВАТЬСЯ!")
            logger.error("   Куки не работают или устарели")
            logger.error("   Требуется получить свежие куки через браузер")
            
            # Сохраняем финальный скриншот
            driver.save_screenshot("final_auth_failed.png")
            
            # Завершаем работу
            return
        
        logger.info("✅ АВТОРИЗАЦИЯ УСПЕШНА!")
        
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
            
            # Делаем заголовок уникальным
            unique_title = make_title_unique(title)
            logger.info(f"Оригинальный заголовок: {title}")
            logger.info(f"Уникальный заголовок: {unique_title}")
            
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
        
        logger.info("=" * 50)
        logger.info(f"📊 ИТОГ: {successful}/{len(posts)}")
        logger.info("=" * 50)
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
