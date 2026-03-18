#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной скрипт для GitHub Actions.
Использует последовательность входа из рабочего проекта без прокси.
"""

import os
import sys
import logging
import time
import random
import json
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импорты модулей проекта
from modules.auth import Auth9111
from modules.telegram_bot_parser import TelegramRSSParser
from modules.publication_api import PublicationAPI
from modules.rubric_mapper import get_rubric_id
from modules.cookie_manager import CookieManager

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
    
    # Проверяем секреты
    required_secrets = ['NINTH_EMAIL', 'NINTH_PASSWORD', 'CHANNEL_ID', 
                        'USER_HASH', 'UUK']
    
    # Опциональный секрет с куками в JSON
    cookies_json = os.environ.get('COOKIES_JSON')
    
    missing_secrets = [s for s in required_secrets if not os.environ.get(s)]
    
    if missing_secrets:
        logger.error(f"❌ Отсутствуют секреты: {', '.join(missing_secrets)}")
        logger.error("Добавьте их в Settings -> Secrets and variables -> Actions")
        return
    
    email = os.environ['NINTH_EMAIL']
    password = os.environ['NINTH_PASSWORD']
    channel_id = os.environ['CHANNEL_ID']
    user_hash = os.environ['USER_HASH']
    uuk = os.environ['UUK']
    
    logger.info("✅ Все основные секреты найдены")
    
    # ШАГ 1: Инициализация авторизации
    logger.info("=" * 60)
    logger.info("🔑 ШАГ 1: Инициализация авторизации")
    logger.info("=" * 60)
    
    auth = Auth9111()
    
    # ШАГ 2: Загрузка кук (сначала из секрета, потом из файлов)
    logger.info("=" * 60)
    logger.info("🍪 ШАГ 2: Загрузка кук")
    logger.info("=" * 60)
    
    cookies = None
    
    # Пробуем загрузить из секрета COOKIES_JSON
    if cookies_json:
        logger.info("📦 Найден секрет COOKIES_JSON, загружаем...")
        cookies = CookieManager.cookies_from_json(cookies_json)
        if cookies:
            logger.info(f"✅ Загружено {len(cookies)} кук из секрета")
    
    # Если нет в секрете, пробуем из файлов
    if not cookies:
        logger.info("🔍 Ищем файлы с куками...")
        cookie_files = list(Path(".").glob("cookies_*.txt"))
        
        if cookie_files:
            # Берем самый свежий файл
            latest_file = max(cookie_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"📄 Загрузка из файла: {latest_file}")
            cookies = CookieManager.load_netscape_cookies(str(latest_file))
    
    # Если все еще нет, создаем из компонентов
    if not cookies:
        logger.info("🔧 Создаем куки из компонентов USER_HASH и UUK")
        cookies = CookieManager.create_cookies_from_parts(
            user_hash=user_hash,
            uuk=uuk
        )
    
    if cookies:
        CookieManager.apply_cookies_to_session(auth.session, cookies)
        logger.info("✅ Куки применены к сессии")
    else:
        logger.warning("⚠️ Нет кук для применения")
    
    # ШАГ 3: Проверка авторизации
    logger.info("=" * 60)
    logger.info("🔑 ШАГ 3: Проверка авторизации")
    logger.info("=" * 60)
    
    if auth.is_authenticated():
        logger.info("✅ Авторизация подтверждена (куки работают)")
    else:
        logger.info("🔑 Куки не работают, выполняем вход...")
        if not auth.login(email, password):
            logger.error("❌ Не удалось авторизоваться")
            return
        logger.info("✅ Авторизация выполнена")
        
        # Сохраняем новые куки для следующих запусков
        new_cookies = auth.session.cookies.get_dict()
        cookies_json = CookieManager.cookies_to_json(new_cookies)
        logger.info("💾 Новые куки получены. Добавьте их в секрет COOKIES_JSON:")
        logger.info("-" * 40)
        print(cookies_json)
        logger.info("-" * 40)
    
    # ШАГ 4: Парсинг Telegram
    logger.info("=" * 60)
    logger.info("📱 ШАГ 4: Парсинг Telegram канала")
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
    
    # ШАГ 5: Публикация постов
    logger.info("=" * 60)
    logger.info("📝 ШАГ 5: Публикация постов")
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
    
    logger.info("=" * 60)
    logger.info(f"📊 ИТОГ: {successful}/{len(posts)} постов опубликовано")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Программа прервана пользователем")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
