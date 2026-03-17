import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем модуль целиком
import modules.github_actions_auth as auth_module
from modules.config import Config
from modules.logger import setup_logging
from modules.publication_api import PublicationAPI
from modules import telegram_bot_parser  # Импортируем модуль целиком
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


def get_telegram_parser():
    """Создает парсер Telegram в зависимости от сигнатуры"""
    try:
        # Пробуем разные варианты инициализации
        if hasattr(telegram_bot_parser, 'TelegramBotParser'):
            ParserClass = telegram_bot_parser.TelegramBotParser
            
            # Пробуем создать с токеном
            try:
                parser = ParserClass(Config.TELEGRAM_TOKEN)
                logger.info("Создан парсер Telegram с токеном")
                return parser
            except TypeError:
                pass
            
            # Пробуем создать с токеном и channel_id
            try:
                parser = ParserClass(Config.TELEGRAM_TOKEN, Config.CHANNEL_ID)
                logger.info("Создан парсер Telegram с токеном и channel_id")
                return parser
            except TypeError:
                pass
            
            # Пробуем создать без аргументов
            try:
                parser = ParserClass()
                logger.info("Создан парсер Telegram без аргументов")
                return parser
            except TypeError:
                pass
        
        logger.error("Не удалось создать парсер Telegram")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при создании парсера: {e}")
        return None


def get_telegram_posts(parser):
    """Получает посты в зависимости от сигнатуры метода"""
    try:
        # Пробуем разные варианты вызова
        if hasattr(parser, 'get_posts'):
            # Пробуем с channel_id и limit
            try:
                posts = parser.get_posts(Config.CHANNEL_ID, limit=Config.POSTS_LIMIT)
                logger.info("Получены посты через get_posts(channel_id, limit)")
                return posts
            except TypeError:
                pass
            
            # Пробуем только с channel_id
            try:
                posts = parser.get_posts(Config.CHANNEL_ID)
                logger.info("Получены посты через get_posts(channel_id)")
                return posts
            except TypeError:
                pass
            
            # Пробуем без аргументов
            try:
                posts = parser.get_posts()
                logger.info("Получены посты через get_posts()")
                return posts
            except TypeError:
                pass
        
        # Если есть другой метод
        if hasattr(parser, 'parse'):
            try:
                posts = parser.parse(Config.CHANNEL_ID, limit=Config.POSTS_LIMIT)
                logger.info("Получены посты через parse()")
                return posts
            except:
                pass
                
    except Exception as e:
        logger.error(f"Ошибка при получении постов: {e}")
    
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
                
        logger.info("✅ Авторизация успешна")
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        return

    # 3. Парсинг Telegram
    parser = get_telegram_parser()
    if not parser:
        logger.error("❌ Не удалось создать парсер Telegram")
        return
        
    posts = get_telegram_posts(parser)

    if not posts:
        logger.warning("❌ Нет постов для публикации")
        return

    logger.info(f"✅ Получено {len(posts)} постов")
    
    # Выводим информацию о первом посте для отладки
    if posts and len(posts) > 0:
        first_post = posts[0]
        logger.info(f"Пример поста - Заголовок: {first_post.get('title', '')[:50]}...")

    # 4. Публикация
    try:
        if not hasattr(auth, 'session'):
            logger.error("❌ У объекта авторизации нет session")
            return
            
        pub_api = PublicationAPI(
            session=auth.session,
            user_hash=Config.USER_HASH,
            uuk=Config.UUK
        )

        successful = 0
        for i, post in enumerate(posts, 1):
            logger.info(f"--- Пост {i}/{len(posts)} ---")
            
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
