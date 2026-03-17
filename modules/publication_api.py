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
            'Cache-Control': 'max-age=0',
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
            # Для длинных заголовков добавляем случайную цифру в конец
            return f"{title} {random.randint(1, 999)}"

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
            logger.info(f"Заголовок изменен для уникальности: {title}")

        # 2. Получаем ID рубрики
        rubric_id = get_rubric_id(rubric_name)
        logger.info(f"Рубрика: '{rubric_name}' (ID: {rubric_id})")

        # 3. Сначала заходим на главную, чтобы получить сессионные куки
        logger.info("Загружаем главную страницу...")
        try:
            main_response = self.session.get('https://9111.ru', timeout=30, allow_redirects=True)
            logger.info(f"Главная страница вернула статус: {main_response.status_code}")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Ошибка при загрузке главной: {e}")

        # 4. Загружаем страницу создания напрямую (без выбора категории)
        logger.info("Загружаем страницу создания публикации...")
        time.sleep(2)
        
        try:
            # Добавляем Referer
            headers = {
                'Referer': 'https://9111.ru/',
            }
            
            get_response = self.session.get(
                self.ADD_TITLE_URL, 
                timeout=30, 
                allow_redirects=True,
                headers=headers
            )
            
            logger.info(f"Статус загрузки страницы: {get_response.status_code}")
            logger.info(f"URL после загрузки: {get_response.url}")
            
            if get_response.status_code != 200:
                logger.error(f"❌ Не удалось загрузить страницу: {get_response.status_code}")
                # Сохраняем часть ответа для отладки
                logger.error(f"Первые 500 символов ответа: {get_response.text[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            return False

        # 5. Извлекаем скрытые поля формы
        soup = BeautifulSoup(get_response.text, "html.parser")
        form = soup.find("form", {"id": "form_create_topic_group"})
        
        form_data = {}
        if form:
            # Собираем все input поля
            for input_tag in form.find_all("input"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    form_data[name] = value
            
            # Собираем textarea
            for textarea in form.find_all("textarea"):
                name = textarea.get("name")
                if name:
                    form_data[name] = textarea.text
            
            logger.info(f"✅ Найдено полей в форме: {len(form_data)}")
        else:
            logger.warning("⚠️ Форма не найдена, будем использовать минимальные данные")

        # 6. Добавляем обязательные поля
        form_data.update({
            "title": title,
            "content": content,
            "rubric_id": str(rubric_id),
            "tags": tags,
            "user_hash": self.user_hash,
            "uuk": self.uuk,
            "submit": "Опубликовать",
        })

        logger.info(f"📦 Отправляем данные (всего полей: {len(form_data)})")

        # 7. Отправляем POST
        try:
            time.sleep(3)
            
            # Подготавливаем заголовки для POST
            post_headers = {
                'Referer': self.ADD_TITLE_URL,
                'Origin': self.BASE_URL,
            }
            
            # Если есть фото, используем multipart/form-data
            if image_path and os.path.exists(image_path):
                logger.info(f"📸 Загружаем фото: {image_path}")
                with open(image_path, 'rb') as f:
                    files = {
                        'images[]': (os.path.basename(image_path), f, 'image/jpeg')
                    }
                    form_data['has_images'] = '1'
                    
                    response = self.session.post(
                        self.ADD_TITLE_URL,
                        data=form_data,
                        files=files,
                        allow_redirects=True,
                        timeout=30,
                        headers=post_headers
                    )
            else:
                # Обычный POST
                response = self.session.post(
                    self.ADD_TITLE_URL,
                    data=form_data,
                    allow_redirects=True,
                    timeout=30,
                    headers=post_headers
                )

            logger.info(f"🌐 Статус ответа: {response.status_code}")
            logger.info(f"📍 URL после запроса: {response.url}")

            # 8. Проверяем результат
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Проверяем на успех
                success_phrases = [
                    "спасибо", "публикация успешно", "ваша публикация",
                    "успешно добавлена", "опубликована", "благодарим"
                ]
                
                for phrase in success_phrases:
                    if phrase in response_text:
                        logger.info(f"✅ Публикация успешно создана! (найдено: '{phrase}')")
                        return True
                
                # Проверяем на ошибку уникальности
                if "уникален" in response_text:
                    logger.warning("⚠️ Заголовок не уникален, пробуем еще раз с другим")
                    # Рекурсивно пробуем с более уникальным заголовком
                    new_title = f"{original_title} {random.randint(1000, 9999)}"
                    return self.create_publication(
                        new_title,
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
                    # Сохраняем ответ для отладки
                    with open(f"debug_response_{int(time.time())}.html", "w") as f:
                        f.write(response.text)
                return False
                
            else:
                logger.error(f"❌ Ошибка HTTP: {response.status_code}")
                return False

        except Exception as e:
            logger.exception(f"❌ Исключение: {e}")
            return False
