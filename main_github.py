#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной скрипт для GitHub Actions.
Использует авторизацию через куки и российские прокси для обхода блокировок.
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

def setup_proxy() -> dict:
    """
    Настройка прокси для обхода блокировок.
    Использует переменную окружения PROXY или возвращает None.
    """
    proxy = os.environ.get('PROXY')
    if proxy:
        logger.info(f"🔌 Настроен прокси: {proxy}")
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    # Список российских прокси для обхода блокировок
    proxy_list = [
        '46.17.47.48:80',
        '46.29.162.166:80',
        '85.198.96.242:3128',
        '46.47.197.210:3128',
        '94.181.80.170:80',
        '94.181.146.80:80',
        '95.167.22.44:3128',
        '95.167.22.45:3128',
        '95.167.22.46:3128',
        '95.167.22.47:3128',
        '95.167.22.48:3128',
        '95.167.22.49:3128',
        '95.167.22.50:3128',
        '95.167.22.51:3128',
        '95.167.22.52:3128',
        '95.167.22.53:3128',
        '95.167.22.54:3128',
        '95.167.22.55:3128',
        '95.167.22.56:3128',
        '95.167.22.57:3128',
        '95.167.22.58:3128',
        '95.167.22.59:3128',
        '95.167.22.60:3128',
        '95.167.22.61:3128',
        '95.167.22.62:3128',
        '95.167.22.63:3128',
        '95.167.22.64:3128',
        '95.167.22.65:3128',
        '95.167.22.66:3128',
        '95.167.22.67:3128',
        '95.167.22.68:3128',
        '95.167.22.69:3128',
        '95.167.22.70:3128'
    ]
    
    # Выбираем случайный прокси
    selected_proxy = random.choice(proxy_list)
    logger.info(f"🔌 Выбран случайный прокси: {selected_proxy}")
    
    return {
        'http': f'http://{selected_proxy}',
        'https': f'http://{selected_proxy}'
    }

def test_proxy(proxies: dict) -> bool:
    """
    Тестирует работоспособность прокси.
    """
    import requests
    
    test_urls = [
        'http://httpbin.org/ip',
        'https://api.ipify.org',
        'http://example.com'
    ]
    
    for url in test_urls:
        try:
            response = requests.get(
                url,
                proxies=proxies,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            if response.status_code == 200:
                logger.info(f"✅ Прокси работает (тест URL: {url})")
                return True
        except Exception as e:
            logger.debug(f"Прокси не работает с {url}: {e}")
            continue
    
    logger.warning("❌ Прокси не прошел тесты")
    return False

def main():
    """Основная функция."""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК 9111 POSTER (GitHub Actions Edition)")
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
    
    # Настройка прокси
    proxies = setup_proxy()
    
    # Тестируем прокси
    if not test_proxy(proxies):
        logger.warning("⚠️ Прокси не работает, пробуем без прокси...")
        proxies = None
    else:
        logger.info("✅ Прокси работает корректно")
    
    # Инициализация авторизации с прокси
    auth = Auth9111(proxies=proxies)
    
    # Проверяем авторизацию
    logger.info("🔑 Проверка авторизации...")
    
    if auth.is_authenticated():
        logger.info("✅ Авторизация подтверждена")
    else:
        logger.info("🔑 Выполняем вход...")
        if not auth.login(os.environ['NINTH_EMAIL'], os.environ['NINTH_PASSWORD']):
            logger.error("❌ Не удалось авторизоваться")
            return
        logger.info("✅ Авторизация выполнена")
        
        # Показываем куки для возможного сохранения
        cookies_json = auth.get_cookies_json()
        logger.info(f"💾 Cookies получены ({len(json.loads(cookies_json))} шт.)")
        logger.info("💡 Совет: сохраните эти cookies в секрет COOKIES_JSON для будущих запусков")
    
    # Парсинг Telegram канала
    logger.info(f"📱 Парсинг Telegram канала: {os.environ['CHANNEL_ID']}")
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
            # Если нет заголовка, используем первые слова текста
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
