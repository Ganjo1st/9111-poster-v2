import logging
import time
import random
import string
from typing import Optional

import requests
from bs4 import BeautifulSoup

from modules.rubric_mapper import get_rubric_id

logger = logging.getLogger(__name__)


class PublicationAPI:
    """Класс для создания публикаций через HTTP-запросы."""

    BASE_URL = "https://9111.ru"
    ADD_URL = f"{BASE_URL}/pubs/add/"
    ADD_TITLE_URL = f"{BASE_URL}/pubs/add/title/"

    def __init__(self, session: requests.Session, user_hash: str, uuk: str):
        """
        :param session: Сессия requests
        :param user_hash: Хеш пользователя
        :param uuk: UUK токен
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        
        # Обновляем заголовки как в браузере
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
        # Устанавливаем куки
        self.session.cookies.set('user_hash', user_hash, domain='.9111.ru', path='/')
        self.session.cookies.set('uuk', uuk, domain='.9111.ru', path='/')
        
        logger.info(f"✅ PublicationAPI инициализирован")

    def _make_title_unique(self, title: str) -> str:
        """Делает заголовок уникальным на 70%"""
        if len(title) < 10:
            # Для коротких заголовков добавляем случайный суффикс
            suffix = ''.join(random.choices(string.ascii_lowercase, k=3))
            return f"{title} {suffix}"
        else:
            # Для длинных заголовков изменяем 30% символов
            chars = list(title)
            num_to_change = max(1, int(len(chars) * 0.3))
            for _ in range(num_to_change):
                idx = random.randint(0, len(chars) - 1)
                # Заменяем на похожий символ или просто другую букву
                if chars[idx].isalpha():
                    if chars[idx].islower():
                        chars[idx] = random.choice('абвгдежзиклмнопрстуфхцчшщъыьэюя')
                    else:
                        chars[idx] = random.choice('АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
            return ''.join(chars)

    def _select_category(self) -> bool:
        """Выбирает категорию 'Новость, статья'"""
        logger.info("Выбираем категорию 'Новость, статья'...")
        
        try:
            response = self.session.get(self.ADD_URL, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ Не удалось загрузить страницу выбора категории: {response.status_code}")
                return False
            
            # Ищем ссылку на создание новости
            soup = BeautifulSoup(response.text, 'html.parser')
            # В реальности тут нужно найти правильную ссылку
            # Пока просто переходим напрямую
            self.session.get(self.ADD_TITLE_URL)
            logger.info("✅ Перешли на страницу создания")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при выборе категории: {e}")
            return False

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

        :param title: Заголовок
        :param content: Текст публикации
        :param rubric_name: Название рубрики
        :param tags: Теги через запятую
        :param image_path: Путь к изображению (опционально)
        :return: True если успешно
        """
        logger.info(f"🚀 Начало публикации: {title[:50]}...")

        # 1. Делаем заголовок уникальным
        original_title = title
        title = self._make_title_unique(title)
        if title != original_title:
            logger.info(f"Заголовок изменен для уникальности: {title[:50]}...")

        # 2. Получаем ID рубрики
        rubric_id = get_rubric_id(rubric_name)
        logger.info(f"Рубрика: '{rubric_name}' (ID: {rubric_id})")

        # 3. Выбираем категорию
        if not self._select_category():
            logger.error("❌ Не удалось выбрать категорию")
            return False

        # 4. Загружаем страницу создания
        logger.info("Загружаем страницу создания...")
        time.sleep(2)
        
        try:
            get_response = self.session.get(self.ADD_TITLE_URL, timeout=30)
            if get_response.status_code != 200:
                logger.error(f"❌ Не удалось загрузить страницу: {get_response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            return False

        # 5. Подготавливаем данные
        form_data = {
            "title": title,
            "content": content,
            "rubric_id": str(rubric_id),
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        }

        # Если есть фото, добавляем
        if image_path:
            try:
                with open(image_path, 'rb') as f:
                    files = {'images[]': (image_path, f, 'image/jpeg')}
                    form_data['has_images'] = '1'
            except Exception as e:
                logger.warning(f"⚠️ Не удалось подготовить фото: {e}")

        logger.info(f"📦 Отправляем данные...")

        # 6. Отправляем POST
        try:
            time.sleep(2)
            
            if image_path and 'files' in locals():
                response = self.session.post(
                    self.ADD_TITLE_URL,
                    data=form_data,
                    files=files,
                    allow_redirects=True,
                    timeout=30,
                )
            else:
                response = self.session.post(
                    self.ADD_TITLE_URL,
                    data=form_data,
                    allow_redirects=True,
                    timeout=30,
                )

            logger.info(f"🌐 Статус ответа: {response.status_code}")
            logger.info(f"📍 URL после запроса: {response.url}")

            # 7. Проверяем результат
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Проверяем на успех
                if "спасибо" in response_text or "публикация успешно" in response_text:
                    logger.info("✅ Публикация успешно создана!")
                    return True
                
                # Проверяем на ошибку уникальности
                if "уникален" in response_text:
                    logger.warning("⚠️ Заголовок не уникален, пробуем еще раз с другим")
                    # Можно рекурсивно попробовать еще раз
                    return self.create_publication(
                        self._make_title_unique(original_title),
                        content,
                        rubric_name,
                        tags,
                        image_path
                    )
                
                # Ищем другие ошибки
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
