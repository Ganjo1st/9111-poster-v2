import os
import logging
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from modules.github_actions_auth import GithubActionsAuth as Auth9111  # или Auth, смотрите что там
from modules.config import Config
from modules.logger import setup_logging
from modules.publication_api import PublicationAPI
from modules.telegram_bot_parser import TelegramBotParser
from modules.rubric_mapper import get_rubric_id

# Настройка логирования
logger = setup_logging()


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster")
    logger.info("=" * 50)

    # 1. Авторизация
    auth = Auth9111()
    if not auth.login(Config.NINTH_EMAIL, Config.NINTH_PASSWORD):
        logger.error("❌ Ошибка авторизации")
        return

    logger.info("✅ Авторизация успешна")

    # 2. Парсинг Telegram
    parser = TelegramBotParser(Config.TELEGRAM_TOKEN)
    posts = parser.get_posts(Config.CHANNEL_ID, limit=Config.POSTS_LIMIT)

    if not posts:
        logger.warning("❌ Нет постов для публикации")
        return

    logger.info(f"✅ Получено {len(posts)} постов")

    # 3. Публикация
    pub_api = PublicationAPI(
        session=auth.session,
        user_hash=Config.USER_HASH,
        uuk=Config.UUK
    )

    successful = 0
    for i, post in enumerate(posts, 1):
        logger.info(f"--- Пост {i}/{len(posts)} ---")
        
        success = pub_api.create_publication(
            title=post.get("title", "")[:100],
            content=post.get("content", ""),
            rubric_name=Config.DEFAULT_RUBRIC,
            tags=Config.DEFAULT_TAGS
        )
        
        if success:
            successful += 1

    logger.info(f"📊 Итог: {successful}/{len(posts)}")


if __name__ == "__main__":
    main()
