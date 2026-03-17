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
        :param session: Авторизованная сессия requests
        :param user_hash: Хеш пользователя (секрет USER_HASH)
        :param uuk: UUK токен (секрет UUK)
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.BASE_URL,
            'Referer': self.ADD_TITLE_URL,
            'Upgrade-Insecure-Requests': '1',
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

        # 2. Сначала загружаем страницу, чтобы получить куки и csrf
        logger.info("Загружаем страницу создания публикации...")
        get_response = self.session.get(self.ADD_TITLE_URL, timeout=30)
        logger.info(f"Статус загрузки страницы: {get_response.status_code}")
        
        if get_response.status_code != 200:
            logger.error(f"❌ Не удалось загрузить страницу: {get_response.status_code}")
            return False

        # 3. Извлекаем скрытые поля формы
        soup = BeautifulSoup(get_response.text, "html.parser")
        form = soup.find("form", {"id": "form_create_topic_group"})
        
        form_data = {}
        if form:
            for input_tag in form.find_all("input", type="hidden"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    form_data[name] = value
            logger.info(f"✅ Найдено скрытых полей: {len(form_data)}")
        else:
            logger.warning("⚠️ Форма не найдена, продолжаем без скрытых полей")

        # 4. Добавляем обязательные поля
        form_data.update({
            "title": title,
            "content": content,
            "rubric_id": str(rubric_id),
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        })

        # 5. Добавляем куки в данные (иногда сайт проверяет)
        cookies = self.session.cookies.get_dict()
        if 'user_hash' in cookies:
            form_data['cookie_user_hash'] = cookies['user_hash']
        if 'uuk' in cookies:
            form_data['cookie_uuk'] = cookies['uuk']

        logger.info(f"📦 Отправляем данные (размер: {len(form_data)} полей)")
        logger.debug(f"Данные: { {k: v[:20] + '...' if isinstance(v, str) and len(v) > 20 else v for k, v in form_data.items()} }")

        # 6. Отправляем POST-запрос
        try:
            response = self.session.post(
                self.ADD_TITLE_URL,
                data=form_data,
                allow_redirects=True,
                timeout=30
            )

            logger.info(f"🌐 Статус ответа: {response.status_code}")
            logger.info(f"📍 URL после запроса: {response.url}")

            if response.status_code == 200:
                # Проверяем разные признаки успеха
                response_text = response.text.lower()
                
                success_indicators = [
                    "спасибо",
                    "публикация успешно",
                    "ваша публикация",
                    "успешно добавлена",
                    "опубликована"
                ]
                
                for indicator in success_indicators:
                    if indicator in response_text:
                        logger.info(f"✅ Найден индикатор успеха: '{indicator}'")
                        return True
                
                # Проверяем наличие ошибок
                soup = BeautifulSoup(response.text, "html.parser")
                error_div = soup.find(id="title_status_save")
                if error_div and error_div.text:
                    error_msg = error_div.text.strip()
                    logger.error(f"❌ Ошибка от сервера: {error_msg}")
                    
                    # Если ошибка про уникальность заголовка
                    if "уникален" in error_msg.lower():
                        logger.warning("⚠️ Заголовок не уникален")
                    return False
                
                # Если нет явных ошибок, считаем успехом
                logger.warning("⚠️ Нет явных признаков успеха или ошибки, но статус 200")
                return True
                
            elif response.status_code == 403:
                logger.error("❌ Ошибка 403 - доступ запрещен. Возможно, нужны дополнительные заголовки")
                logger.error(f"Заголовки запроса: {dict(self.session.headers)}")
                return False
            else:
                logger.error(f"❌ HTTP ошибка: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.exception(f"❌ Исключение при отправке: {e}")
            return False
