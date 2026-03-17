#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import re
import logging
from typing import Optional, List, Tuple

# Добавляем корневую директорию в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования с выводом в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Импортируем наши модули
try:
    from src.browser_manager import BrowserManager
    from src.telegram_parser import TelegramParser
    logger.info("✅ Модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта модулей: {e}")
    logger.error(f"PYTHONPATH: {sys.path}")
    sys.exit(1)


class Post9111:
    """
    Класс для публикации постов из Telegram на сайт 9111.ru
    """
    
    # ID рубрики "Новости" (найден в HTML страницы)
    RUBRIC_NEWS_ID = "382235"
    
    def __init__(self):
        """Инициализация менеджера браузера и парсера Telegram"""
        logger.info("🚀 Инициализация Post9111...")
        self.browser_manager = BrowserManager()
        self.driver = None
        self.wait = None
        self.telegram_parser = TelegramParser()
        logger.info("✅ Post9111 инициализирован")
        
    def setup(self):
        """Запуск браузера и авторизация"""
        logger.info("="*50)
        logger.info("🔧 НАСТРОЙКА БРАУЗЕРА")
        logger.info("="*50)
        
        logger.info("🚀 Запуск браузера...")
        self.driver = self.browser_manager.init_browser()
        
        if not self.driver:
            logger.error("❌ Не удалось запустить браузер")
            return False
            
        self.wait = WebDriverWait(self.driver, 30)
        
        # Выполняем авторизацию через браузер
        logger.info("🔐 Выполняется авторизация на сайте...")
        if not self.browser_manager.login(self.driver):
            logger.error("❌ Не удалось авторизоваться на сайте")
            return False
            
        logger.info("✅ Авторизация успешна")
        return True
        
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            logger.info("🔚 Закрытие браузера...")
            self.driver.quit()
            
    def wait_for_element(self, by: By, value: str, timeout: int = 20) -> Optional[WebElement]:
        """Универсальная функция ожидания элемента"""
        try:
            logger.debug(f"Ожидание элемента: {by} = {value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"❌ Элемент не найден: {by} = {value}")
            # Сохраняем скриншот для отладки
            try:
                screenshot_path = f"screenshots/error_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"📸 Скриншот сохранен: {screenshot_path}")
            except:
                pass
            return None
            
    def safe_send_keys(self, element: WebElement, text: str, clear: bool = True):
        """Безопасный ввод текста"""
        try:
            if clear:
                element.clear()
            time.sleep(0.5)
            element.send_keys(text)
            logger.info(f"📝 Текст введен: {text[:50]}..." if len(text) > 50 else f"📝 Текст введен: {text}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при вводе текста: {e}")
            return False
        
    def extract_links_from_post(self, text: str) -> List[str]:
        """Извлечение ссылок из текста поста"""
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, text)
        
    def upload_image(self, image_path: str) -> bool:
        """
        Загрузка изображения через кнопку + Фото
        """
        logger.info(f"🖼️ Попытка загрузить изображение: {image_path}")
        
        if not os.path.exists(image_path):
            logger.error(f"❌ Файл не найден: {image_path}")
            return False
            
        try:
            # Пробуем найти input file
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if file_inputs:
                logger.info(f"✅ Найдено {len(file_inputs)} input[type=file]")
                file_input = file_inputs[0]
                self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", file_input)
                file_input.send_keys(os.path.abspath(image_path))
                logger.info("✅ Файл отправлен")
                time.sleep(3)
                return True
                
            logger.warning("⚠️ Поле для загрузки не найдено")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке изображения: {e}")
            return False
            
    def create_post(self, title: str, content: str, tags: List[str] = None, image_path: str = None) -> bool:
        """
        Создание публикации на сайте
        """
        logger.info("="*50)
        logger.info("📝 СОЗДАНИЕ ПУБЛИКАЦИИ")
        logger.info("="*50)
        logger.info(f"Заголовок: {title[:100]}...")
        logger.info(f"Длина текста: {len(content)} символов")
        logger.info(f"Теги: {tags}")
        logger.info(f"Изображение: {image_path}")
        
        if not self.driver:
            logger.error("❌ Браузер не инициализирован")
            return False
            
        try:
            # 1. Переходим на страницу создания публикации
            logger.info("🚀 Переход на страницу создания публикации...")
            self.driver.get("https://9111.ru/pubs/add/title/")
            time.sleep(5)
            logger.info(f"📍 Текущий URL: {self.driver.current_url}")
            
            # 2. Ввод заголовка
            logger.info("📝 Поиск поля для заголовка...")
            title_element = self.wait_for_element(By.CSS_SELECTOR, "div#topic_name[contenteditable='true']")
            if not title_element:
                return False
                
            title_element.click()
            self.driver.execute_script("arguments[0].innerText = arguments[1];", title_element, title)
            logger.info(f"✅ Заголовок введен: {title[:50]}...")
            time.sleep(2)
            
            # 3. Выбор рубрики
            logger.info("📌 Поиск выбора рубрики...")
            rubric_select = self.wait_for_element(By.CSS_SELECTOR, "select#rubric_id2")
            if not rubric_select:
                return False
                
            self.driver.execute_script(f"arguments[0].value = '{self.RUBRIC_NEWS_ID}';", rubric_select)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", rubric_select)
            logger.info(f"✅ Выбрана рубрика: Новости (ID: {self.RUBRIC_NEWS_ID})")
            time.sleep(1)
            
            # 4. Ввод текста
            logger.info("✍️ Поиск поля для текста...")
            content_element = self.wait_for_element(By.CSS_SELECTOR, "div#lite_editor[contenteditable='true']")
            if not content_element:
                return False
                
            content_element.click()
            self.driver.execute_script("arguments[0].innerHTML = '';", content_element)
            
            # Разбиваем на абзацы
            paragraphs = content.split('\n')
            for p in paragraphs:
                if p.strip():
                    self.driver.execute_script(f"""
                        var p = document.createElement('p');
                        p.innerText = arguments[1];
                        arguments[0].appendChild(p);
                    """, content_element, p.strip())
            logger.info(f"✅ Текст введен ({len(paragraphs)} абзацев)")
            time.sleep(1)
            
            # 5. Загрузка изображения
            if image_path:
                logger.info("🖼️ Загрузка изображения...")
                if not self.upload_image(image_path):
                    logger.warning("⚠️ Продолжаем без изображения")
            
            # 6. Ввод тегов
            if tags:
                logger.info(f"🏷️ Поиск поля для тегов...")
                tags_input = self.wait_for_element(By.CSS_SELECTOR, "input#tag_list_input")
                if tags_input:
                    self.safe_send_keys(tags_input, ", ".join(tags))
                else:
                    logger.warning("⚠️ Поле для тегов не найдено")
            
            # 7. Отправка формы
            logger.info("📤 Поиск кнопки 'Опубликовать'...")
            publish_button = self.wait_for_element(By.CSS_SELECTOR, "button#button_create_pubs")
            if not publish_button:
                return False
                
            logger.info("📤 Нажатие кнопки...")
            try:
                publish_button.click()
            except Exception as e:
                logger.warning(f"⚠️ Обычный клик не сработал: {e}, пробуем JavaScript...")
                self.driver.execute_script("arguments[0].click();", publish_button)
            
            # 8. Ждем подтверждения
            logger.info("⏳ Ожидание подтверждения публикации...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            if "pubs/add" not in current_url:
                logger.info(f"✅ Публикация создана! URL: {current_url}")
                return True
            else:
                logger.warning("⚠️ Возможно, публикация не создана")
                # Сохраняем скриншот
                self.driver.save_screenshot(f"screenshots/after_publish_{int(time.time())}.png")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при создании публикации: {e}")
            import traceback
            traceback.print_exc()
            # Сохраняем скриншот
            try:
                self.driver.save_screenshot(f"screenshots/error_{int(time.time())}.png")
            except:
                pass
            return False
            
    def process_telegram_post(self, post_text: str, post_date: str = None) -> bool:
        """
        Обработка одного поста из Telegram и публикация на сайт
        """
        logger.info("="*50)
        logger.info(f"📨 ОБРАБОТКА ПОСТА от {post_date if post_date else 'неизвестной даты'}")
        logger.info("="*50)
        logger.info(f"Текст поста: {post_text[:200]}...")
        
        # Очищаем текст от ссылок для публикации
        clean_text = re.sub(r'https?://\S+', '', post_text).strip()
        
        # Создаем заголовок из первых 100 символов
        title = clean_text[:150] if len(clean_text) > 150 else clean_text
        if len(title) < 10:
            logger.warning("⚠️ Заголовок слишком короткий, пропускаем")
            return False
            
        # Создаем теги из ключевых слов
        words = re.findall(r'\b[а-яА-Я]{4,}\b', clean_text.lower())
        unique_words = list(dict.fromkeys(words))[:5]
        tags = unique_words if unique_words else ["новости", "актуально"]
        
        logger.info(f"📝 Подготовлено к публикации:")
        logger.info(f"  Заголовок: {title}")
        logger.info(f"  Теги: {tags}")
        
        # Публикуем пост
        return self.create_post(
            title=title,
            content=clean_text,
            tags=tags,
            image_path=None
        )
        
    def run(self):
        """
        Основной цикл работы
        """
        logger.info("="*50)
        logger.info("🚀 ЗАПУСК ПУБЛИКАТОРА")
        logger.info("="*50)
        
        try:
            # Инициализация
            if not self.setup():
                logger.error("❌ Не удалось настроить браузер")
                return
                
            # Получаем посты из Telegram
            logger.info("📡 Получение постов из Telegram канала...")
            posts = self.telegram_parser.get_channel_posts(limit=5)
            
            if not posts:
                logger.info("😴 Нет новых постов для публикации")
                return
                
            logger.info(f"📊 Найдено постов: {len(posts)}")
            
            # Обрабатываем каждый пост
            for i, post in enumerate(posts, 1):
                logger.info(f"\n📌 Пост {i}/{len(posts)}")
                
                success = self.process_telegram_post(
                    post_text=post['text'],
                    post_date=post.get('date')
                )
                
                if success:
                    logger.info(f"✅ Пост {i} успешно опубликован!")
                else:
                    logger.error(f"❌ Ошибка при публикации поста {i}")
                    
                # Пауза между публикациями
                if i < len(posts):
                    logger.info("⏳ Ожидание 30 секунд...")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            logger.info("⛔ Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()
            logger.info("🏁 Работа завершена")


if __name__ == "__main__":
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК СКРИПТА")
    logger.info("="*50)
    
    # Проверяем переменные окружения
    required_vars = ['TELEGRAM_TOKEN', 'CHANNEL_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют переменные окружения: {missing_vars}")
        logger.info("📝 Добавьте их в GitHub Secrets или .env файл")
        sys.exit(1)
    else:
        logger.info("✅ Все необходимые переменные найдены")
    
    # Запуск
    poster = Post9111()
    poster.run()
