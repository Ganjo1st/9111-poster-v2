import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from modules.rubric_mapper import get_rubric_id

logger = logging.getLogger(__name__)

class PublicationAPI:
    BASE_URL = "https://9111.ru"
    ADD_TITLE_URL = f"{BASE_URL}/pubs/add/title/"

    def __init__(self, session: requests.Session, user_hash: str, uuk: str):
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk

    def create_publication(self, title: str, content: str, rubric_name: str = "новости", tags: str = "", image_path: Optional[str] = None) -> bool:
        logger.info(f"Публикация: {title[:50]}...")

        # 1. Получаем ID рубрики
        rubric_id = get_rubric_id(rubric_name)

        # 2. Загружаем страницу для получения скрытых полей (имитация поведения браузера)
        self.session.get(self.ADD_TITLE_URL)
        time.sleep(2)

        # 3. Отправляем POST-запрос
        data = {
            "title": title,
            "content": content,
            "rubric_id": rubric_id,
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        }

        try:
            response = self.session.post(self.ADD_TITLE_URL, data=data, timeout=30)
            if response.status_code == 200:
                if "спасибо" in response.text.lower() or "публикация успешно" in response.text.lower():
                    logger.info("✅ Успешно!")
                    return True
            logger.warning(f"Ответ: {response.status_code}")
        except Exception as e:
            logger.exception(f"Ошибка: {e}")
        return False
