import os
import time
import re
import logging
from typing import Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from src.browser_manager import BrowserManager
from src.telegram_parser import TelegramParser

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Post9111:
    """
    Класс для публикации постов из Telegram на сайт 9111.ru
    """
    
    # ID рубрики "Новости" (найден в HTML страницы)
    RUBRIC_NEWS_ID = "382235"
    
    def __init__(self):
        """Инициализация менеджера браузера и парсера Telegram"""
        self.browser_manager = BrowserManager()
        self.driver = None
        self.wait = None
        self.telegram_parser = TelegramParser()
        
    def setup(self):
        """Запуск браузера и авторизация"""
        logger.info("Запуск браузера...")
        self.driver = self.browser_manager.init_browser()
        self.wait = WebDriverWait(self.driver, 30)
        
        # Выполняем авторизацию через браузер
        logger.info("Выполняется авторизация на сайте...")
        if not self.browser_manager.login(self.driver):
            raise Exception("Не удалось авторизоваться на сайте")
        logger.info("✅ Авторизация успешна")
        
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            logger.info("Закрытие браузера...")
            self.driver.quit()
            
    def wait_for_element(self, by: By, value: str, timeout: int = 20) -> WebElement:
        """Универсальная функция ожидания элемента"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"❌ Элемент не найден: {by} = {value}")
            raise
            
    def safe_send_keys(self, element: WebElement, text: str, clear: bool = True):
        """Безопасный ввод текста"""
        if clear:
            element.clear()
        time.sleep(0.5)
        element.send_keys(text)
        logger.info(f"📝 Текст введен: {text[:50]}..." if len(text) > 50 else f"📝 Текст введен: {text}")
        
    def extract_links_from_post(self, text: str) -> list:
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
            # Способ 1: Пробуем найти скрытый input file (самый надежный способ)
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if file_inputs:
                logger.info(f"Найдено {len(file_inputs)} input[type=file]")
                file_input = file_inputs[0]
                self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", file_input)
                file_input.send_keys(os.path.abspath(image_path))
                logger.info("✅ Файл отправлен в input")
                time.sleep(3)  # Ждем начала загрузки
                return True
                
            # Способ 2: Ищем кнопку "+ Фото" и кликаем
            photo_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), '+ Фото')]")
            
            if photo_buttons:
                logger.info("Найдена кнопка '+ Фото', пробуем кликнуть")
                try:
                    photo_buttons[0].click()
                    time.sleep(1)
                    
                    # После клика должен появиться input file
                    file_input = self.wait_for_element(By.CSS_SELECTOR, "input[type='file']", timeout=5)
                    file_input.send_keys(os.path.abspath(image_path))
                    logger.info("✅ Файл отправлен после клика")
                    time.sleep(3)
                    return True
                except Exception as e:
                    logger.error(f"Ошибка при клике: {e}")
                    
            # Способ 3: Ищем кнопку через JavaScript
            logger.info("Пробуем через JavaScript...")
            self.driver.execute_script("""
                var btns = document.querySelectorAll('button, a, div');
                for(var i = 0; i < btns.length; i++) {
                    if(btns[i].innerText && btns[i].innerText.includes('+ Фото')) {
                        btns[i].click();
                        return;
                    }
                }
            """)
            time.sleep(1)
            
            file_input = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if file_input:
                file_input[0].send_keys(os.path.abspath(image_path))
                logger.info("✅ Файл отправлен через JS")
                time.sleep(3)
                return True
                
            logger.error("❌ Не удалось найти поле для загрузки фото")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке изображения: {e}")
            return False
            
    def create_post(self, title: str, content: str, tags: list = None, image_path: str = None) -> bool:
        """
        Создание публикации на сайте
        
        Args:
            title: Заголовок публикации
            content: Текст публикации
            tags: Список тегов
            image_path: Путь к изображению (опционально)
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        if not self.driver:
            logger.error("❌ Браузер не инициализирован")
            return False
            
        try:
            # 1. Переходим на страницу создания публикации
            logger.info("🚀 Переход на страницу создания публикации...")
            self.driver.get("https://9111.ru/pubs/add/title/")
            time.sleep(3)
            
            # 2. Ввод заголовка (специальный contenteditable блок)
            logger.info(f"📝 Ввод заголовка: {title[:100]}...")
            title_element = self.wait_for_element(By.CSS_SELECTOR, "div#topic_name[contenteditable='true']")
            title_element.click()
            title_element.clear()
            
            # Используем JavaScript для вставки текста в contenteditable
            self.driver.execute_script("arguments[0].innerText = arguments[1];", title_element, title)
            time.sleep(2)  # Ждем проверки уникальности
            
            # 3. Выбор рубрики "Новости"
            logger.info("📌 Выбор рубрики 'Новости'...")
            rubric_select = self.wait_for_element(By.CSS_SELECTOR, "select#rubric_id2")
            self.driver.execute_script(f"arguments[0].value = '{self.RUBRIC_NEWS_ID}';", rubric_select)
            
            # Триггерим событие change для обновления
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", rubric_select)
            time.sleep(1)
            
            # 4. Ввод текста публикации
            logger.info("✍️ Ввод текста публикации...")
            content_element = self.wait_for_element(By.CSS_SELECTOR, "div#lite_editor[contenteditable='true']")
            content_element.click()
            
            # Очищаем и вставляем текст
            self.driver.execute_script("arguments[0].innerHTML = '';", content_element)
            # Разбиваем текст на абзацы для лучшего форматирования
            paragraphs = content.split('\n')
            for p in paragraphs:
                if p.strip():
                    self.driver.execute_script(f"""
                        var p = document.createElement('p');
                        p.innerText = arguments[1];
                        arguments[0].appendChild(p);
                    """, content_element, p.strip())
            time.sleep(1)
            
            # 5. Загрузка изображения (если есть)
            if image_path:
                self.upload_image(image_path)
            
            # 6. Ввод тегов
            if tags:
                logger.info(f"🏷️ Ввод тегов: {', '.join(tags)}")
                tags_input = self.wait_for_element(By.CSS_SELECTOR, "input#tag_list_input")
                self.safe_send_keys(tags_input, ", ".join(tags))
            
            # 7. Отправка формы
            logger.info("📤 Нажатие кнопки 'Опубликовать'...")
            publish_button = self.wait_for_element(By.CSS_SELECTOR, "button#button_create_pubs")
            
            # Пробуем разные способы клика
            try:
                publish_button.click()
            except:
                try:
                    self.driver.execute_script("arguments[0].click();", publish_button)
                except:
                    logger.error("❌ Не удалось нажать кнопку")
                    return False
            
            # 8. Ждем подтверждения публикации
            logger.info("⏳ Ожидание подтверждения публикации...")
            time.sleep(5)
            
            # Проверяем успех - ищем сообщение об успехе или редирект
            current_url = self.driver.current_url
            if "pubs/add" not in current_url:
                logger.info(f"✅ Публикация создана! Текущий URL: {current_url}")
                return True
            else:
                logger.warning("⚠️ Возможно, публикация не создана, остались на той же странице")
                return False
                
        except TimeoutException as e:
            logger.error(f"❌ Таймаут при ожидании элемента: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def process_telegram_post(self, post_text: str, post_date: str = None) -> bool:
        """
        Обработка одного поста из Telegram и публикация на сайт
        
        Args:
            post_text: Текст поста
            post_date: Дата поста (опционально)
            
        Returns:
            bool: True если успешно
        """
        logger.info("="*50)
        logger.info(f"📨 Обработка поста от {post_date if post_date else 'неизвестной даты'}")
        logger.info("="*50)
        
        # Извлекаем ссылки из текста
        links = self.extract_links_from_post(post_text)
        
        # Извлекаем первое изображение (если есть)
        image_path = None
        for link in links:
            if any(ext in link.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                logger.info(f"🖼️ Найдена ссылка на изображение: {link}")
                # Здесь можно добавить логику скачивания изображения
                # Пока пропускаем, используем только текст
                break
                
        # Очищаем текст от ссылок для публикации (оставляем читабельный текст)
        clean_text = re.sub(r'https?://\S+', '', post_text).strip()
        
        # Создаем заголовок из первых 100 символов
        title = clean_text[:150] if len(clean_text) > 150 else clean_text
        if len(title) < 5:
            logger.warning("⚠️ Заголовок слишком короткий, пропускаем")
            return False
            
        # Создаем теги из ключевых слов
        words = re.findall(r'\b[а-яА-Я]{4,}\b', clean_text.lower())
        unique_words = list(dict.fromkeys(words))[:5]  # До 5 уникальных слов
        tags = unique_words if unique_words else ["новости", "актуально"]
        
        # Публикуем пост
        return self.create_post(
            title=title,
            content=clean_text,
            tags=tags,
            image_path=image_path
        )
        
    def run(self):
        """
        Основной цикл работы: получение постов из Telegram и публикация
        """
        try:
            # Инициализация
            self.setup()
            
            # Получаем посты из Telegram
            logger.info("📡 Получение постов из Telegram канала...")
            posts = self.telegram_parser.get_channel_posts(limit=5)  # Последние 5 постов
            
            if not posts:
                logger.info("😴 Нет новых постов для публикации")
                return
                
            logger.info(f"📊 Найдено постов для обработки: {len(posts)}")
            
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
                    logger.info("⏳ Ожидание 30 секунд перед следующим постом...")
                    time.sleep(30)
                    
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()

if __name__ == "__main__":
    # Запуск при прямом вызове
    poster = Post9111()
    poster.run()
