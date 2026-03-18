#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной скрипт для локального запуска.
Использует модули авторизации и обхода блокировок.
"""

import os
import sys
import logging
import time
import random
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импорты модулей проекта
from modules.auth import Auth9111
from modules.bypass import BypassManager
from modules.telegram_bot_parser import TelegramRSSParser
from modules.publication_api import PublicationAPI
from modules.rubric_mapper import get_rubric_id
from modules.cookie_manager import CookieManager
from modules.proxy_manager import ProxyManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/poster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('9111_poster')

def main():
    """Основная функция."""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК 9111 POSTER")
    logger.info("=" * 60)
    
    # Проверяем наличие всех необходимых переменных окружения
    email = os.environ.get('NINTH_EMAIL')
    password = os.environ.get('NINTH_PASSWORD')
    channel_id = os.environ.get('CHANNEL_ID')
    user_hash = os.environ.get('USER_HASH')
    uuk = os.environ.get('UUK')
    
    if not all([email, password, channel_id, user_hash, uuk]):
        logger.error("❌ Не все переменные окружения установлены!")
        logger.error("Необходимы: NINTH_EMAIL, NINTH_PASSWORD, CHANNEL_ID, USER_HASH, UUK")
        return
    
    logger.info("✅ Все переменные окружения найдены")
    
    # ШАГ 1: Настройка обхода блокировок
    logger.info("=" * 60)
    logger.info("🔧 ШАГ 1: Настройка обхода блокировок")
    logger.info("=" * 60)
    
    bypass = BypassManager()
    
    # Загружаем черный список
    blacklist = bypass.load_blacklist()
    if blacklist:
        logger.info(f"📋 Загружен черный список ({len(blacklist)} записей)")
    
    # Проверяем, не заблокирован ли домен
    if bypass.is_blocked('9111.ru'):
        logger.warning("⚠️ Домен 9111.ru в черном списке, требуется обход")
    
    # ШАГ 2: Загрузка кук
    logger.info("=" * 60)
    logger.info("🍪 ШАГ 2: Загрузка кук")
    logger.info("=" * 60)
    
    cookies = CookieManager.get_cookies_from_files(".")
    
    if not cookies:
        logger.warning("⚠️ Куки не найдены в файлах, пробуем создать из переменных")
        cookies = CookieManager.create_cookies_from_parts(
            user_hash=user_hash,
            uuk=uuk
        )
        logger.info(f"✅ Создано {len(cookies)} кук из переменных")
    
    # ШАГ 3: Поиск рабочего прокси
    logger.info("=" * 60)
    logger.info("🔌 ШАГ 3: Поиск рабочего прокси")
    logger.info("=" * 60)
    
    proxy_manager = ProxyManager()
    working_proxy = proxy_manager.find_working_proxy(max_attempts=None)
    
    if not working_proxy:
        logger.error("❌ НЕ НАЙДЕНО РАБОЧИХ ПРОКСИ!")
        logger.error("Попробуйте запустить без прокси")
        return
    
    logger.info(f"✅ Найден рабочий прокси: {working_proxy}")
    
    # ШАГ 4: Авторизация через прокси
    logger.info("=" * 60)
    logger.info("🔑 ШАГ 4: Авторизация через прокси")
    logger.info("=" * 60)
    
    proxy_dict = proxy_manager.get_proxy_dict(working_proxy)
    auth = Auth9111()
    
    # Применяем прокси к сессии
    auth.session.proxies.update(proxy_dict)
    logger.info("🔌 Прокси применен к сессии")
    
    # Применяем куки
    CookieManager.apply_cookies_to_session(auth.session, cookies)
    logger.info("🍪 Куки применены к сессии")
    
    # Проверяем авторизацию
    if auth.is_authenticated():
        logger.info("✅ Авторизация подтверждена")
    else:
        logger.warning("⚠️ Куки не работают, пробуем выполнить вход...")
        if not auth.login(email, password):
            logger.error("❌ Не удалось авторизоваться")
            return
        logger.info("✅ Авторизация выполнена")
    
    # ШАГ 5: Парсинг Telegram
    logger.info("=" * 60)
    logger.info("📱 ШАГ 5: Парсинг Telegram канала")
    logger.info("=" * 60)
    
    logger.info(f"📱 Канал: {channel_id}")
    tg_parser = TelegramRSSParser()
    
    try:
        posts = tg_parser.get_posts(
            channel_id=channel_id,
            limit=3
        )
        
        if not posts:
            logger.warning("❌ Не получено постов из Telegram")
            return
        
        logger.info(f"✅ Получено {len(posts)} постов из Telegram")
        
    except Exception as e:
        logger.exception(f"❌ Ошибка парсинга Telegram: {e}")
        return
    
    # ШАГ 6: Публикация постов
    logger.info("=" * 60)
    logger.info("📝 ШАГ 6: Публикация постов")
    logger.info("=" * 60)
    
    pub_api = PublicationAPI(
        session=auth.session,
        user_hash=user_hash,
        uuk=uuk
    )
    
    successful = 0
    for i, post in enumerate(posts, 1):
        logger.info("-" * 50)
        logger.info(f"📝 Обработка поста {i}/{len(posts)}")
        logger.info("-" * 50)
        
        title = post.get('title', '')
        if not title:
            content_preview = post.get('content', '')[:100]
            title = f"Новость: {content_preview[:50]}..."
        
        content = post.get('content', '')
        image_url = post.get('image_url')
        
        logger.info(f"📌 Заголовок: {title[:100]}...")
        logger.info(f"📏 Длина текста: {len(content)} символов")
        
        if image_url:
            logger.info(f"🖼️ Есть изображение: {image_url[:50]}...")
        
        success = pub_api.create_publication(
            title=title,
            content=content,
            rubric_name="новости",
            tags="новости, закон, право, общество",
            image_url=image_url
        )
        
        if success:
            successful += 1
            logger.info(f"✅ Пост {i} успешно опубликован")
        else:
            logger.error(f"❌ Ошибка публикации поста {i}")
        
        if i < len(posts):
            delay = random.uniform(5, 10)
            logger.info(f"⏳ Ожидание {delay:.1f} секунд...")
            time.sleep(delay)
    
    # Итоги
    logger.info("=" * 60)
    logger.info(f"📊 ИТОГ: {successful}/{len(posts)} постов опубликовано")
    logger.info(f"📈 Процент успеха: {successful/len(posts)*100:.1f}%")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Программа прервана пользователем")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
