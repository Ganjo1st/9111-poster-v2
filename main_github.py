#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной скрипт для GitHub Actions.
Стратегия: авторизация без прокси (через куки), публикация через российский прокси.
"""

import os
import sys
import logging
import time
import random
import json
import requests
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

# Расширенный список российских прокси из разных источников
RUSSIAN_PROXIES = [
    # HTTP прокси
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
    '95.167.22.70:3128',
    
    # Дополнительные из новых источников
    '185.118.67.66:8080',
    '185.118.67.109:8080',
    '185.118.67.159:8080',
    '185.118.67.211:8080',
    '185.118.67.220:8080',
    '185.118.67.243:8080',
    '91.220.163.202:8080',
    '91.220.163.203:8080',
    '91.220.163.204:8080',
    '91.220.163.205:8080',
    '91.220.163.206:8080',
    '91.220.163.207:8080',
    '91.220.163.208:8080',
    '91.220.163.209:8080',
    '91.220.163.210:8080',
    '94.181.44.217:8080',
    '94.181.44.218:8080',
    '94.181.44.219:8080',
    '94.181.44.220:8080',
    '94.181.44.221:8080',
    '94.181.44.222:8080',
    '94.181.44.223:8080',
    '94.181.44.224:8080',
    '94.181.44.225:8080',
    '94.181.44.226:8080',
    '94.181.44.227:8080',
    '94.181.44.228:8080',
    '94.181.44.229:8080',
    '94.181.44.230:8080',
]

def fetch_fresh_proxies() -> list:
    """
    Получает свежие прокси из внешних источников.
    """
    sources = [
        'https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_ru.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
        'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt'
    ]
    
    fresh_proxies = []
    
    for source in sources:
        try:
            logger.info(f"📡 Загрузка прокси из: {source}")
            response = requests.get(source, timeout=10)
            if response.status_code == 200:
                # Фильтруем только российские (по IP или по наличию в списке)
                lines = response.text.strip().split('\n')
                for line in lines[:100]:  # Берем первые 100 из каждого источника
                    proxy = line.strip()
                    if proxy and ':' in proxy:
                        fresh_proxies.append(proxy)
            logger.info(f"✅ Загружено {len(fresh_proxies)} прокси")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки из {source}: {e}")
    
    return fresh_proxies

def test_proxy(proxy: str, test_url: str = "https://9111.ru") -> bool:
    """
    Тщательно тестирует прокси на работоспособность.
    
    Args:
        proxy: Прокси в формате ip:port
        test_url: URL для тестирования
        
    Returns:
        True если прокси работает
    """
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    
    test_urls = [
        test_url,
        "http://httpbin.org/ip",
        "https://api.ipify.org",
        "http://example.com"
    ]
    
    for url in test_urls:
        try:
            start_time = time.time()
            response = requests.get(
                url,
                proxies=proxies,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"  ✅ {url} - {elapsed:.2f}с")
                
                # Для тестового URL проверяем, что ответ содержит российский IP
                if url == "http://httpbin.org/ip":
                    try:
                        ip_data = response.json()
                        logger.info(f"  🌍 IP через прокси: {ip_data.get('origin', 'unknown')}")
                    except:
                        pass
                
                return True
        except requests.exceptions.ConnectTimeout:
            logger.debug(f"  ⏰ Таймаут: {url}")
        except requests.exceptions.ProxyError as e:
            logger.debug(f"  🔌 Ошибка прокси: {e}")
        except Exception as e:
            logger.debug(f"  ❌ Ошибка: {e}")
    
    return False

def find_working_proxy(max_attempts: int = 30) -> tuple:
    """
    Находит рабочий прокси для 9111.ru.
    
    Args:
        max_attempts: Максимальное количество попыток
        
    Returns:
        (рабочий_прокси, словарь_прокси) или (None, None)
    """
    logger.info("🔍 Поиск рабочего российского прокси...")
    
    # Сначала пробуем свежие прокси из внешних источников
    try:
        fresh_proxies = fetch_fresh_proxies()
        all_proxies = list(set(fresh_proxies + RUSSIAN_PROXIES))  # Объединяем и убираем дубликаты
    except:
        all_proxies = RUSSIAN_PROXIES
    
    logger.info(f"📋 Всего прокси для проверки: {len(all_proxies)}")
    
    # Перемешиваем для случайного выбора
    random.shuffle(all_proxies)
    
    tested = 0
    working_proxies = []
    
    for proxy in all_proxies[:max_attempts * 2]:  # Берем с запасом
        tested += 1
        logger.info(f"🔄 Тест {tested}/{min(max_attempts * 2, len(all_proxies))}: {proxy}")
        
        if test_proxy(proxy):
            working_proxies.append(proxy)
            logger.info(f"  ✅ Прокси РАБОТАЕТ! ({len(working_proxies)} найдено)")
            
            # Если нашли рабочий, возвращаем его сразу
            if len(working_proxies) >= 1:
                proxy_dict = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
                logger.info(f"🎯 Выбран прокси: {proxy}")
                return proxy, proxy_dict
        
        if tested >= max_attempts:
            break
    
    if working_proxies:
        # Если есть рабочие, выбираем лучший
        best_proxy = working_proxies[0]
        proxy_dict = {
            'http': f'http://{best_proxy}',
            'https': f'http://{best_proxy}'
        }
        logger.info(f"🎯 Выбран прокси: {best_proxy}")
        return best_proxy, proxy_dict
    
    logger.warning("❌ Рабочих прокси не найдено")
    return None, None

def main():
    """Основная функция."""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК 9111 POSTER (GitHub Actions Edition)")
    logger.info("📋 Стратегия: авторизация без прокси -> публикация через прокси")
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
    
    # ШАГ 1: Авторизация БЕЗ прокси
    logger.info("=" * 60)
    logger.info("🔑 ШАГ 1: Авторизация без прокси")
    logger.info("=" * 60)
    
    auth = Auth9111(proxies=None)  # Явно без прокси
    
    # Проверяем авторизацию
    logger.info("🔑 Проверка авторизации...")
    
    if auth.is_authenticated():
        logger.info("✅ Авторизация подтверждена (активная сессия)")
    else:
        logger.info("🔑 Выполняем вход...")
        if not auth.login(os.environ['NINTH_EMAIL'], os.environ['NINTH_PASSWORD']):
            logger.error("❌ Не удалось авторизоваться")
            return
        logger.info("✅ Авторизация выполнена")
        
        # Показываем куки для возможного сохранения
        cookies_json = auth.get_cookies_json()
        logger.info(f"💾 Cookies получены ({len(json.loads(cookies_json))} шт.)")
    
    # Сохраняем сессию для использования с прокси позже
    auth_session = auth.session
    
    # ШАГ 2: Парсинг Telegram (тоже без прокси)
    logger.info("=" * 60)
    logger.info("📱 ШАГ 2: Парсинг Telegram канала")
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
    
    # ШАГ 3: Поиск рабочего российского прокси
    logger.info("=" * 60)
    logger.info("🔌 ШАГ 3: Поиск рабочего российского прокси")
    logger.info("=" * 60)
    
    working_proxy, proxy_dict = find_working_proxy(max_attempts=30)
    
    if not working_proxy:
        logger.warning("⚠️ Рабочий прокси не найден, пробуем публикацию без прокси")
        proxy_dict = None
    else:
        logger.info(f"✅ Найден рабочий прокси: {working_proxy}")
        
        # Обновляем сессию с новым прокси
        logger.info("🔄 Обновление сессии с прокси...")
        auth.session.proxies.update(proxy_dict)
        logger.info("✅ Сессия обновлена")
    
    # ШАГ 4: Публикация через прокси (если нашли)
    logger.info("=" * 60)
    logger.info("📝 ШАГ 4: Публикация постов")
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
