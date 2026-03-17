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
        
        # Пробуем метод get_updates
        if hasattr(parser, 'get_updates'):
            logger.info("Вызываем parser.get_updates()")
            try:
                updates = parser.get_updates()
                if updates:
                    logger.info(f"✅ Получено {len(updates)} обновлений")
                    # Преобразуем updates в посты
                    posts = []
                    for update in updates:
                        if 'message' in update:
                            msg = update['message']
                            post = {
                                'title': msg.get('text', '')[:100],
                                'content': msg.get('text', ''),
                                'date': msg.get('date', '')
                            }
                            posts.append(post)
                    if posts:
                        logger.info(f"✅ Преобразовано {len(posts)} постов из get_updates")
                        return posts
            except Exception as e:
                logger.warning(f"Ошибка в get_updates(): {e}")
        
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
        logger.info(f"📄 Пример поста:")
        logger.info(f"  Заголовок: {first_post.get('title', '')[:100]}")
        logger.info(f"  Контент: {first_post.get('content', '')[:100]}...")

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
