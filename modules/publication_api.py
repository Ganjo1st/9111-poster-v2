import logging
import time
import gzip
import zlib
from typing import Optional

import requests
from bs4 import BeautifulSoup

from modules.rubric_mapper import get_rubric_id

logger = logging.getLogger(__name__)


def decompress_response(response):
    """Пытается декомпрессировать ответ, если он сжат"""
    content_encoding = response.headers.get('Content-Encoding', '')
    
    if 'gzip' in content_encoding:
        try:
            return gzip.decompress(response.content).decode('utf-8')
        except:
            pass
    elif 'deflate' in content_encoding:
        try:
            return zlib.decompress(response.content).decode('utf-8')
        except:
            pass
    
    # Если не получилось декомпрессировать, пробуем как есть
    try:
        return response.text
    except:
        return str(response.content)


class PublicationAPI:
    """Класс для создания публикаций через HTTP-запросы (без Selenium)."""

    BASE_URL = "https://9111.ru"
    ADD_TITLE_URL = f"{BASE_URL}/pubs/add/title/"

    def __init__(self, session: requests.Session, user_hash: str, uuk: str):
        """
        :param session: Сессия requests (может быть неавторизованной)
        :param user_hash: Хеш пользователя (секрет USER_HASH)
        :param uuk: UUK токен (секрет UUK)
        """
        self.session = session
        self.user_hash = user_hash
        self.uuk = uuk
        
        # Важно: сначала обновляем заголовки
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',  # Разрешаем сжатие
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
        
        logger.info(f"✅ PublicationAPI инициализирован с user_hash={user_hash[:10]}...")

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

        # 2. Сначала заходим на главную, чтобы получить сессионные куки
        logger.info("Загружаем главную страницу...")
        try:
            main_response = self.session.get('https://9111.ru', timeout=30, allow_redirects=True)
            logger.info(f"Главная страница вернула статус: {main_response.status_code}")
            logger.info(f"Заголовки ответа: {dict(main_response.headers)}")
            
            # Пробуем декомпрессировать ответ
            main_text = decompress_response(main_response)
            logger.info(f"Длина декомпрессированного ответа: {len(main_text)}")
            
            # Проверяем куки после загрузки главной
            cookies_dict = self.session.cookies.get_dict()
            logger.info(f"Текущие куки: {list(cookies_dict.keys())}")
            
        except Exception as e:
            logger.warning(f"Ошибка при загрузке главной: {e}")

        # 3. Загружаем страницу создания публикации
        logger.info("Загружаем страницу создания публикации...")
        time.sleep(2)  # Небольшая задержка
        
        try:
            get_response = self.session.get(self.ADD_TITLE_URL, timeout=30, allow_redirects=True)
            logger.info(f"Статус загрузки страницы: {get_response.status_code}")
            logger.info(f"URL после загрузки: {get_response.url}")
            logger.info(f"Заголовки ответа: {dict(get_response.headers)}")
            
            if get_response.status_code != 200:
                logger.error(f"❌ Не удалось загрузить страницу: {get_response.status_code}")
                # Пробуем декомпрессировать ответ для отладки
                response_text = decompress_response(get_response)
                logger.error(f"Первые 500 символов ответа: {response_text[:500]}")
                return False
                
            # Декомпрессируем ответ для парсинга
            response_text = decompress_response(get_response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке страницы: {e}")
            return False

        # 4. Извлекаем скрытые поля формы
        soup = BeautifulSoup(response_text, "html.parser")
        form = soup.find("form", {"id": "form_create_topic_group"})
        
        form_data = {}
        if form:
            # Собираем все input поля
            for input_tag in form.find_all("input"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if name:
                    form_data[name] = value
                    logger.debug(f"Найдено поле: {name}={value[:20] if len(value) > 20 else value}")
            
            # Собираем textarea
            for textarea in form.find_all("textarea"):
                name = textarea.get("name")
                if name:
                    form_data[name] = textarea.text
                    logger.debug(f"Найдено textarea: {name}")
            
            logger.info(f"✅ Найдено полей в форме: {len(form_data)}")
        else:
            logger.warning("⚠️ Форма не найдена, продолжаем без скрытых полей")
            # Сохраняем часть HTML для отладки
            logger.error(f"Первые 1000 символов HTML: {response_text[:1000]}")

        # 5. Добавляем обязательные поля
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
        
        # Логируем только имена полей для безопасности
        logger.info(f"Имена полей: {list(form_data.keys())}")

        # 6. Отправляем POST-запрос
        try:
            # Добавляем задержку перед POST
            time.sleep(3)
            
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
            logger.info(f"Заголовки ответа: {dict(response.headers)}")

            # Декомпрессируем ответ для проверки
            response_text = decompress_response(response)

            if response.status_code == 200:
                # Проверяем разные признаки успеха
                response_text_lower = response_text.lower()
                
                success_indicators = [
                    "спасибо",
                    "публикация успешно",
                    "ваша публикация",
                    "успешно добавлена",
                    "опубликована",
                    "благодарим"
                ]
                
                for indicator in success_indicators:
                    if indicator in response_text_lower:
                        logger.info(f"✅ Найден индикатор успеха: '{indicator}'")
                        return True
                
                # Проверяем наличие ошибок
                soup = BeautifulSoup(response_text, "html.parser")
                error_div = soup.find(id="title_status_save")
                if error_div and error_div.text:
                    error_msg = error_div.text.strip()
                    logger.error(f"❌ Ошибка от сервера: {error_msg}")
                    
                    # Если ошибка про уникальность заголовка
                    if "уникален" in error_msg.lower():
                        logger.warning("⚠️ Заголовок не уникален")
                    return False
                
                # Проверяем, нет ли перенаправления на страницу с публикацией
                if response.url != self.ADD_TITLE_URL:
                    logger.info(f"✅ Перенаправление на {response.url} - вероятно успех")
                    return True
                
                # Если нет явных ошибок, считаем успехом
                logger.warning("⚠️ Нет явных признаков успеха или ошибки, но статус 200")
                return True
                
            elif response.status_code == 403:
                logger.error("❌ Ошибка 403 - доступ запрещен")
                logger.error(f"Заголовки запроса: {dict(self.session.headers)}")
                logger.error(f"Cookies: {dict(self.session.cookies.get_dict())}")
                return False
            else:
                logger.error(f"❌ HTTP ошибка: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.exception(f"❌ Исключение при отправке: {e}")
            return False
