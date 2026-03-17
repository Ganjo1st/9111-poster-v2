import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем модуль целиком, чтобы не зависеть от имени класса
import modules.github_actions_auth as auth_module
from modules.config import Config
from modules.logger import setup_logging
from modules.publication_api import PublicationAPI
from modules.telegram_bot_parser import TelegramBotParser
from modules.rubric_mapper import get_rubric_id

# Настройка логирования
logger = setup_logging()


def get_auth_class():
    """Получает класс авторизации из модуля (может называться по-разному)"""
    possible_names = ['Auth9111', 'GithubActionsAuth', 'Auth', 'GitHubActionsAuth']
    
    for name in possible_names:
        if hasattr(auth_module, name):
            logger.info(f"Найден класс авторизации: {name}")
            return getattr(auth_module, name)
    
    # Если ничего не найдено, выводим все атрибуты модуля для отладки
    logger.error("Не найден класс авторизации. Доступные атрибуты:")
    for attr in dir(auth_module):
        if not attr.startswith('_'):
            logger.error(f"  - {attr}")
    return None


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
        auth = AuthClass()
        if not auth.login(Config.NINTH_EMAIL, Config.NINTH_PASSWORD):
            logger.error("❌ Ошибка авторизации")
            return
        logger.info("✅ Авторизация успешна")
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        return

    # 3. Парсинг Telegram
    try:
        parser = TelegramBotParser(Config.TELEGRAM_TOKEN)
        posts = parser.get_posts(Config.CHANNEL_ID, limit=Config.POSTS_LIMIT)

        if not posts:
            logger.warning("❌ Нет постов для публикации")
            return

        logger.info(f"✅ Получено {len(posts)} постов")
    except Exception as e:
        logger.error(f"❌ Ошибка при парсинге Telegram: {e}")
        return

    # 4. Публикация
    try:
        pub_api = PublicationAPI(
            session=auth.session,
            user_hash=Config.USER_HASH,
            uuk=Config.UUK
        )

        successful = 0
        for i, post in enumerate(posts, 1):
            logger.info(f"--- Пост {i}/{len(posts)} ---")
            
            # Получаем данные поста
            title = post.get("title", "")[:100]
            content = post.get("content", "")
            
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
