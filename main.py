import os
import sys
import pickle
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем модуль целиком
import modules.github_actions_auth as auth_module
import modules.telegram_bot_parser as tg_module
from modules.config import Config
from modules.logger import setup_logging
from modules.publication_api import PublicationAPI
from modules.rubric_mapper import get_rubric_id

# Настройка логирования
logger = setup_logging()


def get_auth_class():
    """Получает класс авторизации из модуля"""
    possible_names = ['GitHubActionsAuth', 'Auth9111', 'GithubActionsAuth', 'Auth']
    
    for name in possible_names:
        if hasattr(auth_module, name):
            logger.info(f"Найден класс авторизации: {name}")
            return getattr(auth_module, name)
    
    logger.error("Не найден класс авторизации")
    return None


def get_session_from_auth(auth):
    """Пытается получить session из объекта auth разными способами"""
    
    # Способ 1: прямой атрибут session
    if hasattr(auth, 'session'):
        logger.info("✅ Найден auth.session")
        return auth.session
    
    # Способ 2: атрибут _session
    if hasattr(auth, '_session'):
        logger.info("✅ Найден auth._session")
        return auth._session
    
    # Способ 3: метод get_session()
    if hasattr(auth, 'get_session') and callable(auth.get_session):
        try:
            session = auth.get_session()
            if session:
                logger.info("✅ Получена сессия через get_session()")
                return session
        except:
            pass
    
    # Способ 4: используем driver для создания сессии
    if hasattr(auth, 'driver') and auth.driver:
        logger.info("🔄 Пробуем создать сессию из driver")
        try:
            import requests
            from selenium.webdriver.common.by import By
            
            session = requests.Session()
            # Копируем cookies из driver в session
            for cookie in auth.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Добавляем стандартные headers
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            logger.info("✅ Сессия создана из cookies driver")
            return session
        except Exception as e:
            logger.warning(f"Не удалось создать сессию из driver: {e}")
    
    # Способ 5: загружаем cookies из файла
    if hasattr(auth, 'cookies_file') and auth.cookies_file:
        logger.info(f"🔄 Пробуем загрузить cookies из {auth.cookies_file}")
        try:
            import requests
            with open(auth.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            logger.info("✅ Сессия создана из cookies файла")
            return session
        except Exception as e:
            logger.warning(f"Не удалось загрузить cookies: {e}")
    
    logger.error("❌ Не удалось получить session ни одним способом")
    return None


def get_telegram_posts():
    """Получает посты из Telegram используя правильные методы"""
    logger.info("🤖 Попытка получить посты из Telegram...")
    
    if not hasattr(tg_module, 'TelegramBotParser'):
        logger.error("❌ Класс TelegramBotParser не найден")
        return []
    
    ParserClass = tg_module.TelegramBotParser
    
    try:
        # Создаем парсер с обоими аргументами
        logger.info(f"Создаем парсер с token и channel_id")
        parser = ParserClass(Config.TELEGRAM_TOKEN, Config.CHANNEL_ID)
        logger.info("✅ Парсер создан успешно")
        
        # Пробуем метод parse_channel_posts
        if hasattr(parser, 'parse_channel_posts'):
            logger.info("Вызываем parser.parse_channel_posts()")
            try:
                posts = parser.parse_channel_posts()
                if posts:
                    logger.info(f"✅ Получено {len(posts)} постов через parse_channel_posts()")
                    return posts
                else:
                    logger.warning("parse_channel_posts() вернул пустой список")
            except Exception as e:
                logger.warning(f"Ошибка в parse_channel_posts(): {e}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании парсера: {e}")
        logger.error(f"   Ожидаемая сигнатура: __init__(bot_token, channel_id)")
    
    logger.warning("❌ Не удалось получить посты")
    return []


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster")
    logger.info("=" * 50)

    # 1. Получаем класс авторизации
    AuthClass = get_auth_class()
    if not AuthClass:
        logger.error("❌ Не удалось найти класс авторизации")
        return

    # 2. Авторизация
    try:
        auth = AuthClass(Config.NINTH_EMAIL, Config.NINTH_PASSWORD)
        
        if hasattr(auth, 'login'):
            if not auth.login():
                logger.error("❌ Ошибка авторизации")
                return
        
        logger.info("✅ Авторизация выполнена")
        
        # Получаем session
        session = get_session_from_auth(auth)
        
        if session is None:
            logger.error("❌ Не удалось получить session")
            return
            
        logger.info("✅ Сессия получена успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        return

    # 3. Парсинг Telegram
    posts = get_telegram_posts()

    if not posts:
        logger.warning("❌ Нет постов для публикации")
        return

    logger.info(f"✅ Получено {len(posts)} постов")
    
    # Выводим информацию о первом посте для отладки
    if posts and len(posts) > 0:
        first_post = posts[0]
        logger.info(f"📄 Пример поста:")
        logger.info(f"  Заголовок: {first_post.get('title', '')[:100]}")
        logger.info(f"  Контент: {first_post.get('content', '')[:100]}...")

    # 4. Публикация
    try:
        pub_api = PublicationAPI(
            session=session,
            user_hash=Config.USER_HASH,
            uuk=Config.UUK
        )

        successful = 0
        for i, post in enumerate(posts, 1):
            logger.info(f"--- 📝 Пост {i}/{len(posts)} ---")
            
            title = post.get("title", "")[:100]
            content = post.get("content", "")
            
            if not title or not content:
                logger.warning(f"⚠️ Пост {i} пропущен: нет заголовка или контента")
                continue
                
            logger.info(f"Заголовок: {title}")
            
            success = pub_api.create_publication(
                title=title,
                content=content,
                rubric_name=Config.DEFAULT_RUBRIC,
                tags=Config.DEFAULT_TAGS
            )
            
            if success:
                successful += 1
                logger.info(f"✅ Пост {i} опубликован")
            else:
                logger.error(f"❌ Ошибка публикации поста {i}")

        logger.info(f"📊 Итог: {successful}/{len(posts)} постов опубликовано")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при публикации: {e}")
        return


if __name__ == "__main__":
    main()
