import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from modules.rubric_mapper import get_rubric_id

logger = logging.getLogger(__name__)


class PublicationAPI:
    """Класс для создания публикаций через HTTP-запросы (без Selenium)."""

    BASE_URL = "https://9111.ru"
    ADD_TITLE_URL = f"{BASE_URL}/pubs/add/title/"

    def __init__(self, session: requests.Session, user_hash: str, uuk: str):
        """
        :param session: Авторизованная сессия requests (из github_actions_auth)
        :param user_hash: Хеш пользователя (секрет USER_HASH)
        :param uuk: UUK токен (секрет UUK)
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        self.session.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.BASE_URL,
        })

    def create_publication(
        self,
        title: str,
        content: str,
        rubric_name: str = "новости",
        tags: str = "",
    ) -> bool:
        """
        Создает публикацию на сайте.

        :param title: Заголовок
        :param content: Текст публикации
        :param rubric_name: Название рубрики (например, "новости")
        :param tags: Теги через запятую
        :return: True если успешно
        """
        logger.info(f"🚀 Начало публикации: {title[:50]}...")

        # 1. Получаем ID рубрики
        rubric_id = get_rubric_id(rubric_name)
        logger.info(f"Рубрика: '{rubric_name}' (ID: {rubric_id})")

        # 2. Имитируем заход на страницу (получаем куки и т.д.)
        self.session.get(self.ADD_TITLE_URL)
        time.sleep(2)

        # 3. Подготавливаем данные формы
        form_data = {
            "title": title,
            "content": content,
            "rubric_id": rubric_id,
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        }

        # 4. Отправляем POST-запрос
        try:
            response = self.session.post(self.ADD_TITLE_URL, data=form_data, timeout=30)

            if response.status_code != 200:
                logger.error(f"HTTP ошибка: {response.status_code}")
                return False

            # 5. Анализируем ответ
            if "спасибо" in response.text.lower() or "публикация успешно" in response.text.lower():
                logger.info("✅ Публикация успешно создана!")
                return True
            else:
                # Ищем возможные ошибки
                soup = BeautifulSoup(response.text, "html.parser")
                error_div = soup.find(id="title_status_save")
                if error_div and error_div.text:
                    logger.error(f"Ошибка от сервера: {error_div.text.strip()}")
                else:
                    logger.warning("Не удалось определить результат. Возможно, публикация создана.")
                return False

        except Exception as e:
            logger.exception(f"❌ Исключение при отправке: {e}")
            return False
