import os
import time
import logging
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

from modules.exceptions import PublicationError
from modules.logger import log_function_call

logger = logging.getLogger(__name__)


class PublicationManager:
    """
    Класс для создания публикации на сайте 9111.ru через Selenium.
    Предполагается, что пользователь уже авторизован, и куки переданы в драйвер.
    """

    def __init__(self, driver: webdriver, rubric_id: int, default_tags: str = ""):
        """
        :param driver: Экземпляр Selenium WebDriver с уже авторизованной сессией.
        :param rubric_id: ID рубрики для публикации (например, 382235 для "Новости").
        :param default_tags: Теги по умолчанию.
        """
        self.driver = driver
        self.rubric_id = rubric_id
        self.default_tags = default_tags
        self.wait = WebDriverWait(driver, 20)  # Увеличиваем таймаут

    def _wait_and_find(self, by, value, timeout=15):
        """Утилита для ожидания и поиска элемента."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            logger.error(f"Элемент не найден: {by}={value}")
            # Делаем скриншот для отладки
            screenshot_path = f"logs/debug_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Скриншот сохранен: {screenshot_path}")
            raise

    def _safe_click(self, element):
        """Безопасный клик с прокруткой до элемента и обработкой перехватов."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            # Пробуем обычный клик
            element.click()
        except ElementClickInterceptedException:
            # Если перехвачено, пробуем через JavaScript
            logger.warning("Клик перехвачен, пробуем через JavaScript")
            self.driver.execute_script("arguments[0].click();", element)

    @log_function_call
    def navigate_to_publication_page(self):
        """Переход на страницу создания публикации."""
        logger.info("Переход на страницу создания публикации...")
        
        # Пробуем прямой переход
        self.driver.get("https://9111.ru/pubs/add/title/")
        time.sleep(3)
        
        # Проверяем, что мы на правильной странице
        current_url = self.driver.current_url
        if "/pubs/add/title/" in current_url:
            logger.info("✅ На странице создания публикации")
            return
            
        # Если нет, пробуем через /pubs/add/
        logger.info("Пробуем через /pubs/add/")
        self.driver.get("https://9111.ru/pubs/add/")
        time.sleep(2)
        
        try:
            # Ищем ссылку "Новость, статья"
            news_link = self._wait_and_find(By.XPATH, "//a[contains(text(), 'Новость') or contains(text(), 'статья')]", timeout=5)
            self._safe_click(news_link)
            logger.info("Выбран тип публикации: Новость, статья")
        except TimeoutException:
            # Если не нашли, пробуем другую ссылку
            try:
                # Может быть кнопка "Создать публикацию"
                create_btn = self._wait_and_find(By.XPATH, "//a[contains(@href, '/pubs/add/title/')]", timeout=5)
                self._safe_click(create_btn)
            except:
                logger.warning("Не удалось найти ссылку, пробуем прямой переход")
                self.driver.get("https://9111.ru/pubs/add/title/")
        
        time.sleep(3)

    @log_function_call
    def set_title(self, title: str):
        """Ввод заголовка публикации."""
        logger.info(f"Установка заголовка: {title[:50]}...")
        
        # Ограничиваем длину заголовка (макс 150 символов)
        if len(title) > 150:
            title = title[:147] + "..."
            
        title_div = self._wait_and_find(By.ID, "topic_name")
        self._safe_click(title_div)
        time.sleep(0.5)
        
        # Очищаем поле
        title_div.clear()
        title_div.send_keys(Keys.CONTROL + "a")
        title_div.send_keys(Keys.DELETE)
        
        # Вводим заголовок по частям (иногда помогает)
        for char in title:
            title_div.send_keys(char)
            time.sleep(0.01)
            
        logger.info(f"✅ Заголовок введен ({len(title)} символов)")

    @log_function_call
    def set_rubric(self):
        """Выбор рубрики из выпадающего списка по ID."""
        logger.info(f"Выбор рубрики с ID: {self.rubric_id}")
        
        select_element = self._wait_and_find(By.ID, "rubric_id2")
        
        # Пробуем через JavaScript (надежнее)
        self.driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, select_element, str(self.rubric_id))
        
        time.sleep(1)
        logger.info(f"✅ Рубрика выбрана")

    @log_function_call
    def set_content(self, content: str):
        """Ввод текста публикации в визуальный редактор."""
        logger.info("Ввод текста публикации...")
        
        editor_div = self._wait_and_find(By.ID, "lite_editor")
        self._safe_click(editor_div)
        time.sleep(0.5)
        
        # Очищаем редактор
        editor_div.send_keys(Keys.CONTROL + "a")
        editor_div.send_keys(Keys.DELETE)
        time.sleep(0.5)
        
        # Вставляем текст
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                # Вставляем строку
                editor_div.send_keys(line.strip())
                # Добавляем переносы строк для абзацев
                if i < len(lines) - 1:
                    editor_div.send_keys(Keys.SHIFT + Keys.ENTER + Keys.SHIFT + Keys.ENTER)
            time.sleep(0.1)
            
        logger.info(f"✅ Текст введен ({len(content)} символов)")

    @log_function_call
    def upload_photo(self, image_path: str):
        """Загрузка фото."""
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Файл не найден: {image_path}")
            return False
            
        logger.info(f"Загрузка изображения: {image_path}")
        
        try:
            # В headless режиме используем прямой upload через input
            # Ищем input type="file"
            file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
            if file_input:
                file_input.send_keys(os.path.abspath(image_path))
                logger.info("✅ Фото загружено через input")
                time.sleep(3)
                return True
        except NoSuchElementException:
            logger.warning("Input для файла не найден, ищем кнопку + Фото")
        
        # Если input не нашли, ищем кнопку
        try:
            photo_button = self._wait_and_find(By.XPATH, 
                "//*[contains(text(), '+ Фото')] | //*[contains(@class, 'addPhoto')] | //button[contains(text(), 'Фото')]",
                timeout=5
            )
            self._safe_click(photo_button)
            time.sleep(2)
            
            # В headless режиме это может не сработать, но пробуем
            if not os.environ.get('DISPLAY'):  # Если headless
                logger.warning("Headless режим: upload через input не поддерживается")
                # Пытаемся найти input после клика
                file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                if file_input:
                    file_input.send_keys(os.path.abspath(image_path))
                    logger.info("✅ Фото загружено")
                    time.sleep(3)
                    return True
            else:
                # В режиме с GUI используем pyautogui
                pyautogui.write(os.path.abspath(image_path))
                pyautogui.press('enter')
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"Ошибка загрузки фото: {e}")
            return False
            
        return False

    @log_function_call
    def set_tags(self, tags: str = None):
        """Установка тегов."""
        if tags is None:
            tags = self.default_tags
        if not tags:
            logger.info("Теги не указаны, пропускаем")
            return
            
        logger.info(f"Установка тегов: {tags}")
        
        try:
            tags_input = self._wait_and_find(By.ID, "tag_list_input")
            tags_input.clear()
            tags_input.send_keys(tags)
            time.sleep(1)
            logger.info("✅ Теги добавлены")
        except:
            logger.warning("Не удалось добавить теги")

    @log_function_call
    def submit(self):
        """Нажатие кнопки 'Опубликовать'."""
        logger.info("Отправка формы...")
        
        submit_button = self._wait_and_find(By.ID, "button_create_pubs")
        self._safe_click(submit_button)
        
        # Ждем результат
        time.sleep(5)
        
        # Проверяем результат
        try:
            status_div = self.driver.find_element(By.ID, "title_status_save")
            if status_div.text:
                logger.info(f"Статус: {status_div.text}")
                if "ошибка" in status_div.text.lower():
                    raise PublicationError(f"Ошибка: {status_div.text}")
        except NoSuchElementException:
            pass
            
        logger.info("✅ Форма отправлена")

    @log_function_call
    def create_publication(self, title: str, content: str, tags: str = None, image_path: str = None):
        """
        Полный цикл создания публикации.
        """
        try:
            self.navigate_to_publication_page()
            self.set_title(title)
            self.set_rubric()
            self.set_content(content)
            if image_path:
                self.upload_photo(image_path)
            self.set_tags(tags)
            self.submit()
            logger.info("🎉 Публикация успешно создана!")
            return True
            
        except Exception as e:
            logger.exception(f"❌ Ошибка при создании публикации: {e}")
            # Сохраняем скриншот
            screenshot_path = f"logs/error_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Скриншот ошибки: {screenshot_path}")
            
            # Сохраняем HTML страницы для отладки
            html_path = f"logs/error_{int(time.time())}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"HTML страницы: {html_path}")
            
            return False
