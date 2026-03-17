import os
import sys
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


def debug_telegram_module():
    """Выводит отладочную информацию о модуле telegram_bot_parser"""
    logger.info("🔍 Отладка модуля telegram_bot_parser:")
    
    # Смотрим все классы и функции в модуле
    for attr_name in dir(tg_module):
        if not attr_name.startswith('_'):
            attr = getattr(tg_module, attr_name)
            attr_type = type(attr).__name__
            logger.info(f"  - {attr_name}: {attr_type}")
    
    # Проверяем наличие класса TelegramBotParser
    if hasattr(tg_module, 'TelegramBotParser'):
        ParserClass = tg_module.TelegramBotParser
        logger.info(f"✅ Найден класс TelegramBotParser")
        
        # Смотрим методы класса
        for method_name in dir(ParserClass):
            if not method_name.startswith('_'):
                method = getattr(ParserClass, method_name)
                if callable(method):
                    logger.info(f"    Метод: {method_name}")
    else:
        logger.error("❌ Класс TelegramBotParser не найден")


def get_telegram_posts():
    """Универсальная функция для получения постов из Telegram"""
    logger.info("🤖 Попытка получить посты из Telegram...")
    
    # Пробуем разные способы получить посты
    
    # Способ 1: Если есть функция get_posts в модуле
    if hasattr(tg_module, 'get_posts'):
        try:
            logger.info("Пробуем tg_module.get_posts()")
            posts = tg_module.get_posts(Config.CHANNEL_ID, Config.TELEGRAM_TOKEN)
            if posts:
                logger.info(f"✅ Получено {len(posts)} постов через get_posts")
                return posts
        except Exception as e:
            logger.warning(f"Не сработало: {e}")
    
    # Способ 2: Если есть класс с методом parse
    if hasattr(tg_module, 'TelegramBotParser'):
        ParserClass = tg_module.TelegramBotParser
        
        # Пробуем разные сигнатуры конструктора
        try:
            logger.info("Пробуем parser = TelegramBotParser(token)")
            parser = ParserClass(Config.TELEGRAM_TOKEN)
            
            # Пробуем разные методы получения постов
            if hasattr(parser, 'get_posts'):
                try:
                    posts = parser.get_posts(Config.CHANNEL_ID)
                    if posts:
                        logger.info(f"✅ Получено {len(posts)} постов через parser.get_posts(channel_id)")
                        return posts
                except:
                    pass
                    
            if hasattr(parser, 'parse'):
                try:
                    posts = parser.parse(Config.CHANNEL_ID)
                    if posts:
                        logger.info(f"✅ Получено {len(posts)} постов через parser.parse(channel_id)")
                        return posts
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Не сработало с token: {e}")
        
        # Пробуем без аргументов
        try:
            logger.info("Пробуем parser = TelegramBotParser()")
            parser = ParserClass()
            
            if hasattr(parser, 'get_posts'):
                try:
                    posts = parser.get_posts(Config.CHANNEL_ID)
                    if posts:
                        logger.info(f"✅ Получено {len(posts)} постов через parser.get_posts(channel_id)")
                        return posts
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Не сработало без аргументов: {e}")
    
    # Способ 3: Пробуем напрямую импортировать функции
    try:
        if hasattr(tg_module, 'parse_channel'):
            logger.info("Пробуем tg_module.parse_channel()")
            posts = tg_module.parse_channel(Config.CHANNEL_ID, Config.TELEGRAM_TOKEN)
            if posts:
                logger.info(f"✅ Получено {len(posts)} постов через parse_channel")
                return posts
    except:
        pass
    
    logger.warning("❌ Не удалось получить посты ни одним способом")
    return []


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster")
    logger.info("=" * 50)

    # Отладка Telegram модуля
    debug_telegram_module()

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
    posts = get_telegram_posts()

    if not posts:
        logger.warning("❌ Нет постов для публикации")
        return

    logger.info(f"✅ Получено {len(posts)} постов")
    
    # Выводим информацию о первом посте для отладки
    if posts and len(posts) > 0:
        first_post = posts[0]
        logger.info(f"Пример поста:")
        logger.info(f"  Заголовок: {first_post.get('title', '')[:50]}...")
        logger.info(f"  Контент: {first_post.get('content', '')[:50]}...")

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
