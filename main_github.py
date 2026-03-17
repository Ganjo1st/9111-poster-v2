#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной скрипт для GitHub Actions.
ФИНАЛЬНАЯ СТРАТЕГИЯ: прокси с первого запроса!
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
from modules.github_actions_auth import Auth9111
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
    logger.info("🚀 ЗАПУСК 9111 POSTER (ФИНАЛЬНАЯ ВЕРСИЯ)")
    logger.info("📋 Стратегия: прокси -> куки -> авторизация -> публикация")
    logger.info("=" * 60)
    
    # Проверяем наличие всех необходимых секретов
    required_secrets = ['NINTH_EMAIL', 'NINTH_PASSWORD', 'CHANNEL_ID', 
                        'TELEGRAM_TOKEN', 'USER_HASH', 'UUK']
    
    missing_secrets = [s for s in required_secrets if not os.environ.get(s)]
    
    if missing_secrets:
        logger.error(f"❌ Отсутствуют секреты: {', '.join(missing_secrets)}")
        logger.error("Пожалуйста, добавьте их в настройках репозитория -> Secrets and variables -> Actions")
        return
    
    logger.info("✅ Все секреты найдены")
    
    # ШАГ 1: Загрузка кук из файлов
    logger.info("=" * 60)
    logger.info("🍪 ШАГ 1: Загрузка кук из файлов")
    logger.info("=" * 60)
    
    cookies = CookieManager.get_cookies_from_files(".")
    
    if not cookies:
        logger.warning("⚠️ Куки не найдены в файлах, пробуем создать из секретов")
        # Создаем куки из секретов
        cookies = CookieManager.create_cookies_from_parts(
            user_hash=os.environ['USER_HASH'],
            uuk=os.environ['UUK']
        )
        logger.info(f"✅ Создано {len(cookies)} кук из секретов")
    
    logger.info(f"🍪 Загруженные куки: {list(cookies.keys())}")
    
    # ШАГ 2: Поиск рабочего российского прокси с поддержкой HTTPS
    logger.info("=" * 60)
    logger.info("🔌 ШАГ 2: Поиск рабочего российского прокси (с HTTPS)")
    logger.info("=" * 60)
    
    proxy_manager = ProxyManager()
    
    # Ищем прокси специально для 9111.ru
    working_proxy = proxy_manager.find_working_proxy(
        max_attempts=100,  # Увеличили до 100 попыток
        target_url="https://9111.ru"
    )
    
    if not working_proxy:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Не найден рабочий российский прокси с HTTPS")
        logger.error("Без HTTPS прокси сайт блокирует все запросы. Завершаем работу.")
        return
    
    logger.info(f"✅ Найден рабочий прокси: {working_proxy}")
    
    # ШАГ 3: Создание сессии СРАЗУ с прокси
    logger.info("=" * 60)
    logger.info("🔑 ШАГ 3: Создание сессии с прокси и применение кук")
    logger.info("=" * 60)
    
    # Получаем словарь прокси
    proxy_dict = proxy_manager.get_proxy_dict(working_proxy)
    
    # Создаем сессию СРАЗУ с прокси
    auth = Auth9111(proxies=proxy_dict)
    
    # Применяем куки к сессии
    CookieManager.apply_cookies_to_session(auth.session, cookies)
    logger.info("🍪 Куки применены к сессии с прокси")
    
    # ШАГ 4: Проверка авторизации (уже через прокси)
    logger.info("🔑 Проверка авторизации через прокси...")
    
    if auth.is_authenticated():
        logger.info("✅ Авторизация подтверждена (куки работают через прокси)")
    else:
        logger.warning("⚠️ Куки не работают через прокси, пробуем выполнить вход...")
        logger.info("🔑 Выполняем вход через прокси...")
        
        if not auth.login(os.environ['NINTH_EMAIL'], os.environ['NINTH_PASSWORD']):
            logger.error("❌ Не удалось авторизоваться даже через прокси")
            return
        
        logger.info("✅ Авторизация выполнена через прокси")
        
        # Сохраняем новые куки для будущих запусков
        new_cookies = auth.session.cookies.get_dict()
        logger.info(f"💾 Получены новые куки ({len(new_cookies)} шт.)")
    
    # ШАГ 5: Парсинг Telegram (без прокси - это отдельно)
    logger.info("=" * 60)
    logger.info("📱 ШАГ 5: Парсинг Telegram канала")
    logger.info("=" * 60)
    
    logger.info(f"📱 Канал: {os.environ['CHANNEL_ID']}")
    tg_parser = TelegramRSSParser()
    
    try:
        posts = tg_parser.get_posts(
            channel_id=os.environ['CHANNEL_ID'],
            limit=3
        )
        
        if not posts:
            logger.warning("❌ Не получено постов из Telegram")
            return
        
        logger.info(f"✅ Получено {len(posts)} постов из Telegram")
        
        # Выводим первые несколько постов для отладки
        for i, post in enumerate(posts[:2], 1):
            title = post.get('title', 'Без заголовка')
            logger.info(f"📄 Пост {i}: {title[:100]}...")
            
    except Exception as e:
        logger.exception(f"❌ Ошибка парсинга Telegram: {e}")
        return
    
    # ШАГ 6: Публикация постов (уже через прокси)
    logger.info("=" * 60)
    logger.info("📝 ШАГ 6: Публикация постов")
    logger.info("=" * 60)
    
    # Инициализация API публикаций
    pub_api = PublicationAPI(
        session=auth.session,
        user_hash=os.environ['USER_HASH'],
        uuk=os.environ['UUK']
    )
    
    # Публикация каждого поста
    successful = 0
    for i, post in enumerate(posts, 1):
        logger.info("-" * 50)
        logger.info(f"📝 Обработка поста {i}/{len(posts)}")
        logger.info("-" * 50)
        
        # Извлекаем данные поста
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
        
        # Создаем публикацию
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
        
        # Задержка между публикациями
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
