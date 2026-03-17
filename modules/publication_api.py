import logging
import time
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from modules.exceptions import PublicationError
from modules.logger import log_function_call

logger = logging.getLogger(__name__)


class PublicationAPI:
    """
    Класс для создания публикаций через прямой HTTP API сайта 9111.ru.
    Работает поверх авторизованной сессии requests.
    """

    BASE_URL = "https://9111.ru"
    ADD_PUB_URL = f"{BASE_URL}/pubs/add/"
    ADD_TITLE_URL = f"{BASE_URL}/pubs/add/title/"

    # ID рубрик из HTML-кода
    RUBRIC_IDS = {
        "новости": 382235,
        "автомобили": 9121,
        "бизнес": 7907625,
        "жилье": 156463,
        "дтп": 144192,
        "юридическая публикация": 7685949,
        "общество": 401453,
        "политика": 489293,
        # Добавьте нужные рубрики
    }

    def __init__(self, session: requests.Session, user_hash: str, uuk: str):
        """
        :param session: Авторизованная сессия requests (из Auth9111)
        :param user_hash: Хеш пользователя из site_vars (секрет USER_HASH)
        :param uuk: UUK токен (секрет UUK)
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        self.session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.BASE_URL,
        })

    def _get_form_data(self, html_content: str) -> Dict[str, str]:
        """Извлекает скрытые поля формы (CSRF токены и т.д.)"""
        soup = BeautifulSoup(html_content, "html.parser")
        form = soup.find("form", {"id": "form_create_topic_group"})
        if not form:
            return {}

        data = {}
        for input_tag in form.find_all("input", type="hidden"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                data[name] = value
        return data

    @log_function_call
    def check_title_uniqueness(self, title: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет уникальность заголовка.
        Возвращает (уникален_ли, сообщение_об_ошибке)
        """
        logger.info(f"Проверка заголовка на уникальность: {title[:50]}...")

        # Эндпоинт для проверки (нужно найти в network запросах)
        check_url = f"{self.BASE_URL}/pubs/add/check_title/"
        data = {
            "title": title,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
        }

        try:
            response = self.session.post(check_url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    return True, None
                else:
                    return False, result.get("message", "Заголовок не уникален")
        except Exception as e:
            logger.warning(f"Ошибка при проверке заголовка: {e}")

        # Если не удалось проверить, считаем что уникален (риск)
        return True, None

    @log_function_call
    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Загружает изображение на сервер.
        Возвращает ID загруженного файла или None.
        """
        if not image_path:
            return None

        logger.info(f"Загрузка изображения: {image_path}")
        upload_url = f"{self.BASE_URL}/pubs/add/upload_image/"

        try:
            with open(image_path, "rb") as f:
                files = {"file": (image_path, f, "image/jpeg")}
                data = {
                    "user_hash": self.user_hash,
                    "uuk": self.uuk,
                }
                response = self.session.post(upload_url, files=files, data=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    file_id = result.get("file_id")
                    logger.info(f"Изображение загружено, ID: {file_id}")
                    return file_id
                else:
                    logger.error(f"Ошибка загрузки: {result}")
            else:
                logger.error(f"HTTP ошибка при загрузке: {response.status_code}")
        except Exception as e:
            logger.exception(f"Исключение при загрузке фото: {e}")

        return None

    @log_function_call
    def create_publication(
        self,
        title: str,
        content: str,
        rubric_name: str = "новости",
        tags: str = "",
        image_path: Optional[str] = None,
    ) -> bool:
        """
        Создает публикацию на сайте.

        :param title: Заголовок (должен быть уникален на 70%)
        :param content: Текст публикации
        :param rubric_name: Название рубрики (из RUBRIC_IDS)
        :param tags: Теги через запятую
        :param image_path: Путь к изображению (опционально)
        :return: True если успешно
        """
        logger.info(f"🚀 Начало создания публикации: {title[:50]}...")

        # 1. Проверяем уникальность заголовка
        is_unique, error_msg = self.check_title_uniqueness(title)
        if not is_unique:
            logger.error(f"Заголовок не уникален: {error_msg}")
            # Можно добавить модификацию заголовка
            title = f"{title} ."  # Добавляем точку для уникальности
            logger.info(f"Заголовок изменен на: {title[:50]}...")

        # 2. Получаем ID рубрики
        rubric_id = self.RUBRIC_IDS.get(rubric_name.lower())
        if not rubric_id:
            logger.error(f"Рубрика '{rubric_name}' не найдена. Доступны: {list(self.RUBRIC_IDS.keys())}")
            return False

        # 3. Загружаем изображение, если есть
        file_id = None
        if image_path:
            file_id = self.upload_image(image_path)
            time.sleep(1)

        # 4. Сначала заходим на страницу, чтобы получить актуальные токены
        logger.info("Загрузка страницы создания публикации...")
        response = self.session.get(self.ADD_TITLE_URL)
        if response.status_code != 200:
            logger.error(f"Не удалось загрузить страницу: {response.status_code}")
            return False

        # 5. Извлекаем скрытые поля формы
        form_data = self._get_form_data(response.text)
        if not form_data:
            logger.warning("Не удалось найти скрытые поля формы")

        # 6. Подготавливаем данные для отправки
        post_data = {
            **form_data,
            "title": title,
            "content": content,
            "rubric_id": rubric_id,
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        }

        # Если есть загруженное изображение
        if file_id:
            post_data["attached_images[]"] = file_id

        # 7. Отправляем POST-запрос
        logger.info("Отправка данных публикации...")
        try:
            response = self.session.post(
                self.ADD_TITLE_URL,
                data=post_data,
                allow_redirects=True,
                timeout=30,
            )

            # Проверяем результат
            if response.status_code == 200:
                # Ищем индикатор успеха
                if "публикация успешно" in response.text.lower() or "спасибо" in response.text.lower():
                    logger.info("✅ Публикация успешно создана!")
                    return True
                else:
                    # Проверяем наличие ошибок
                    soup = BeautifulSoup(response.text, "html.parser")
                    error_div = soup.find(id="title_status_save")
                    if error_div and error_div.text:
                        logger.error(f"Ошибка от сервера: {error_div.text.strip()}")
                    else:
                        logger.warning("Не удалось определить результат. Возможно, публикация создана.")
                        # Сохраняем ответ для отладки
                        with open(f"logs/response_{int(time.time())}.html", "w", encoding="utf-8") as f:
                            f.write(response.text)
                        return True
            else:
                logger.error(f"HTTP ошибка: {response.status_code}")

        except Exception as e:
            logger.exception(f"Исключение при отправке: {e}")

        return False

    def modify_title_for_uniqueness(self, title: str) -> str:
        """Добавляет случайный символ для обеспечения уникальности"""
        import random
        import string

        # Если заголовок короткий, добавляем случайную букву
        if len(title) < 150:
            suffix = random.choice(string.ascii_lowercase)
            return f"{title} {suffix}"
        return title
