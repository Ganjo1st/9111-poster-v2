"""
Модуль для создания публикаций на 9111.ru через HTTP API.
Работает без Selenium, используя авторизованную сессию requests.
"""
import logging
import time
import random
import os
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from modules.rubric_mapper import get_rubric_id

logger = logging.getLogger(__name__)

class PublicationAPI:
    """
    Класс для создания публикаций на 9111.ru через HTTP-запросы.
    Полностью эмулирует поведение браузера при отправке формы.
    """
    
    BASE_URL = "https://9111.ru"
    ADD_PUB_URL = f"{BASE_URL}/pubs/add/"
    ADD_TITLE_URL = f"{BASE_URL}/pubs/add/title/"
    CHECK_TITLE_URL = f"{BASE_URL}/pubs/add/check_title/"
    UPLOAD_IMAGE_URL = f"{BASE_URL}/pubs/add/upload_image/"
    
    def __init__(self, session: requests.Session, user_hash: str, uuk: str):
        """
        Инициализация API публикаций.
        
        Args:
            session: Авторизованная сессия requests (из github_actions_auth)
            user_hash: Хеш пользователя (секрет USER_HASH)
            uuk: UUK токен (секрет UUK)
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        
        # Заголовки как у реального браузера
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        })
    
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Случайная задержка для имитации человеческого поведения."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _get_form_data(self, html_content: str) -> Dict[str, str]:
        """
        Извлекает скрытые поля формы (CSRF токены и т.д.).
        
        Args:
            html_content: HTML страницы
            
        Returns:
            Словарь со скрытыми полями формы
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        form = soup.find('form', {'id': 'form_create_topic_group'})
        
        if not form:
            logger.warning("Форма с id='form_create_topic_group' не найдена")
            return {}
        
        hidden_fields = {}
        for input_tag in form.find_all('input', type='hidden'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                hidden_fields[name] = value
                
        logger.debug(f"Найдено скрытых полей: {len(hidden_fields)}")
        return hidden_fields
    
    def check_title_uniqueness(self, title: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет уникальность заголовка через AJAX-запрос.
        
        Args:
            title: Заголовок для проверки
            
        Returns:
            (уникален_ли, сообщение_об_ошибке)
        """
        logger.info(f"Проверка заголовка на уникальность: {title[:50]}...")
        
        # Имитация загрузки страницы перед проверкой
        self.session.get(self.ADD_TITLE_URL)
        self._random_delay(1, 2)
        
        data = {
            "title": title,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
        }
        
        try:
            response = self.session.post(
                self.CHECK_TITLE_URL,
                data=data,
                timeout=15,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": self.ADD_TITLE_URL,
                }
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") == "ok":
                        logger.info("✅ Заголовок уникален")
                        return True, None
                    else:
                        message = result.get("message", "Заголовок не уникален")
                        logger.warning(f"❌ Заголовок не уникален: {message}")
                        return False, message
                except ValueError:
                    logger.warning("Не удалось распарсить JSON ответ")
            else:
                logger.warning(f"HTTP ошибка при проверке: {response.status_code}")
                
        except Exception as e:
            logger.exception(f"Ошибка при проверке заголовка: {e}")
        
        # В случае ошибки считаем, что заголовок уникален (риск)
        return True, None
    
    def modify_title_for_uniqueness(self, title: str) -> str:
        """
        Модифицирует заголовок для обеспечения уникальности.
        
        Args:
            title: Исходный заголовок
            
        Returns:
            Модифицированный заголовок
        """
        import hashlib
        import time
        
        # Добавляем уникальный суффикс на основе времени
        suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        
        if len(title) < 150:
            return f"{title} [{suffix}]"
        else:
            # Если заголовок длинный, заменяем последние символы
            return title[:-10] + f" [{suffix}]"
    
    def download_image_from_url(self, image_url: str) -> Optional[str]:
        """
        Скачивает изображение по URL и сохраняет временно.
        
        Args:
            image_url: URL изображения
            
        Returns:
            Путь к скачанному файлу или None
        """
        if not image_url:
            return None
        
        logger.info(f"📥 Скачивание изображения: {image_url[:50]}...")
        
        try:
            # Создаем временную директорию
            temp_dir = Path("temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            # Генерируем имя файла
            ext = os.path.splitext(urlparse(image_url).path)[1]
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
            
            filename = f"image_{int(time.time())}_{random.randint(1000, 9999)}{ext}"
            file_path = temp_dir / filename
            
            # Скачиваем изображение
            response = self.session.get(
                image_url,
                timeout=30,
                stream=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"✅ Изображение скачано: {file_path}")
                return str(file_path)
            else:
                logger.error(f"❌ Ошибка скачивания: {response.status_code}")
                
        except Exception as e:
            logger.exception(f"❌ Ошибка при скачивании: {e}")
        
        return None
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Загружает изображение на сервер.
        
        Args:
            image_path: Путь к файлу изображения
            
        Returns:
            ID загруженного файла или None
        """
        if not image_path or not os.path.exists(image_path):
            return None
            
        logger.info(f"Загрузка изображения: {image_path}")
        
        try:
            with open(image_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(image_path), f, 'image/jpeg')
                }
                data = {
                    'user_hash': self.user_hash,
                    'uuk': self.uuk,
                }
                
                response = self.session.post(
                    self.UPLOAD_IMAGE_URL,
                    files=files,
                    data=data,
                    timeout=30,
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": self.ADD_TITLE_URL,
                    }
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get("status") == "ok":
                            file_id = result.get("file_id")
                            logger.info(f"✅ Изображение загружено, ID: {file_id}")
                            return file_id
                        else:
                            logger.error(f"Ошибка загрузки: {result}")
                    except ValueError:
                        logger.error("Не удалось распарсить JSON ответ")
                else:
                    logger.error(f"HTTP ошибка при загрузке: {response.status_code}")
                    
        except Exception as e:
            logger.exception(f"Исключение при загрузке фото: {e}")
            
        return None
    
    def create_publication(
        self,
        title: str,
        content: str,
        rubric_name: str = "новости",
        tags: str = "",
        image_url: Optional[str] = None,
        max_retries: int = 2,
    ) -> bool:
        """
        Создает публикацию на сайте.
        
        Args:
            title: Заголовок публикации
            content: Текст публикации
            rubric_name: Название рубрики (по умолчанию "новости")
            tags: Теги через запятую
            image_url: URL изображения (опционально)
            max_retries: Максимальное количество попыток при ошибке уникальности
            
        Returns:
            True если публикация успешно создана
        """
        logger.info("=" * 60)
        logger.info(f"🚀 Начало создания публикации")
        logger.info(f"📝 Заголовок: {title[:100]}...")
        logger.info(f"📏 Длина текста: {len(content)} символов")
        logger.info("=" * 60)
        
        # Скачиваем изображение, если есть URL
        image_path = None
        if image_url:
            image_path = self.download_image_from_url(image_url)
        
        current_title = title
        attempt = 0
        
        while attempt <= max_retries:
            attempt += 1
            
            if attempt > 1:
                logger.info(f"Попытка #{attempt} с модифицированным заголовком")
            
            # 1. Проверяем уникальность заголовка
            is_unique, error_msg = self.check_title_uniqueness(current_title)
            
            if not is_unique:
                logger.warning(f"Заголовок не уникален, модифицируем...")
                current_title = self.modify_title_for_uniqueness(title)
                continue
            
            # 2. Получаем ID рубрики
            rubric_id = get_rubric_id(rubric_name)
            logger.info(f"📌 Рубрика: '{rubric_name}' (ID: {rubric_id})")
            
            # 3. Загружаем страницу для получения скрытых полей
            logger.info("📡 Загрузка страницы создания публикации...")
            response = self.session.get(self.ADD_TITLE_URL)
            
            if response.status_code != 200:
                logger.error(f"❌ Не удалось загрузить страницу: {response.status_code}")
                return False
            
            self._random_delay(2, 3)
            
            # 4. Извлекаем скрытые поля формы
            form_data = self._get_form_data(response.text)
            
            # 5. Загружаем изображение, если есть
            file_id = None
            if image_path:
                file_id = self.upload_image(image_path)
                self._random_delay(1, 2)
                
                # Удаляем временный файл после загрузки
                try:
                    os.remove(image_path)
                    logger.debug(f"Временный файл удален: {image_path}")
                except:
                    pass
            
            # 6. Подготавливаем данные для отправки
            post_data = {
                **form_data,  # Добавляем скрытые поля
                "title": current_title,
                "content": content,
                "rubric_id": rubric_id,
                "tags": tags,
                "user_hash": self.user_hash,
                "uuk": self.uuk,
                "submit": "Опубликовать",
            }
            
            # Добавляем ID изображения, если оно загружено
            if file_id:
                post_data["attached_images[]"] = file_id
            
            # 7. Отправляем POST-запрос
            logger.info("📤 Отправка данных публикации...")
            
            try:
                response = self.session.post(
                    self.ADD_TITLE_URL,
                    data=post_data,
                    allow_redirects=True,
                    timeout=30,
                    headers={
                        "Referer": self.ADD_TITLE_URL,
                    }
                )
                
                # 8. Анализируем результат
                if response.status_code in [200, 302]:
                    response_text = response.text.lower()
                    
                    # Проверяем признаки успеха
                    success_indicators = [
                        "спасибо",
                        "публикация успешно",
                        "ваша публикация отправлена",
                        "пост добавлен",
                    ]
                    
                    for indicator in success_indicators:
                        if indicator in response_text:
                            logger.info("✅ Публикация успешно создана!")
                            
                            # Сохраняем URL созданной публикации
                            if hasattr(response, 'url') and response.url != self.ADD_TITLE_URL:
                                logger.info(f"🔗 URL: {response.url}")
                            
                            return True
                    
                    # Проверяем наличие ошибок
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Ищем ошибки в специальном div
                    error_div = soup.find(id="title_status_save")
                    if error_div and error_div.text.strip():
                        error_text = error_div.text.strip()
                        logger.error(f"❌ Ошибка от сервера: {error_text}")
                        
                        # Если ошибка о неуникальности, пробуем еще раз
                        if "уникальн" in error_text.lower():
                            current_title = self.modify_title_for_uniqueness(title)
                            continue
                        
                        return False
                    
                    # Ищем другие возможные ошибки
                    error_messages = soup.find_all(class_=["error", "alert", "warning"])
                    for error in error_messages:
                        if error.text.strip():
                            logger.warning(f"⚠️ Предупреждение: {error.text.strip()}")
                    
                    # Если нет явных ошибок, вероятно успех
                    logger.info("✅ Публикация вероятно создана (нет явных ошибок)")
                    return True
                    
                else:
                    logger.error(f"❌ HTTP ошибка: {response.status
