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
        :param session: Сессия requests (должна быть авторизованной)
        :param user_hash: Хеш пользователя (секрет USER_HASH)
        :param uuk: UUK токен (секрет UUK)
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        
        # Обновляем заголовки
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Устанавливаем куки
        self.session.cookies.set('user_hash', user_hash, domain='.9111.ru', path='/')
        self.session.cookies.set('uuk', uuk, domain='.9111.ru', path='/')
        
        logger.info(f"✅ PublicationAPI инициализирован")

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

        # 2. Подготавливаем данные формы
        form_data = {
            "title": title,
            "content": content,
            "rubric_id": str(rubric_id),
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        }

        logger.info(f"📦 Отправляем данные...")

        # 3. Отправляем POST-запрос
        try:
            # Добавляем задержку
            time.sleep(2)
            
            response = self.session.post(
                self.ADD_TITLE_URL,
                data=form_data,
                allow_redirects=True,
                timeout=30,
                headers={
                    'Referer': self.ADD_TITLE_URL,
                    'Origin': self.BASE_URL,
                }
            )

            logger.info(f"🌐 Статус ответа: {response.status_code}")
            logger.info(f"📍 URL после запроса: {response.url}")

            if response.status_code == 200:
                # Проверяем текст ответа
                if "спасибо" in response.text.lower() or "публикация успешно" in response.text.lower():
                    logger.info("✅ Публикация успешно создана!")
                    return True
                else:
                    # Ищем ошибки
                    soup = BeautifulSoup(response.text, "html.parser")
                    error_div = soup.find(id="title_status_save")
                    if error_div and error_div.text:
                        logger.error(f"❌ Ошибка: {error_div.text.strip()}")
                    else:
                        logger.warning("⚠️ Неизвестный ответ, но статус 200")
                    return False
            else:
                logger.error(f"❌ Ошибка HTTP: {response.status_code}")
                return False

        except Exception as e:
            logger.exception(f"❌ Исключение: {e}")
            return False
