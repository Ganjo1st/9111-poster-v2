import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем путь к проекту для импортов
sys.path.insert(0, str(Path(__file__).parent))

from modules.auth import Auth9111
from modules.bypass import BypassManager
from modules.config import Config
from modules.logger import setup_logging, log_function_call
from modules.publication_api import PublicationAPI
from modules.rubric_mapper import get_rubric_id
from modules.telegram_parser import TelegramRSSParser
from modules import utils

# Настройка логирования
logger = setup_logging()


@log_function_call
def main():
    """Основная функция."""
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster v2 (GitHub Actions Edition)")
    logger.info("=" * 50)

    # 1. Получаем секреты из окружения
    email = os.getenv("NINTH_EMAIL")
    password = os.getenv("NINTH_PASSWORD")
    channel_id = os.getenv("CHANNEL_ID")
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    user_hash = os.getenv("USER_HASH")
    uuk = os.getenv("UUK")

    if not all([email, password, channel_id, user_hash, uuk]):
        logger.error("❌ Не все секреты установлены!")
        return

    # 2. Инициализация менеджера обхода блокировок
    bypass = BypassManager(user_agent=Config.USER_AGENT_9111)

    # 3. Авторизация на 9111.ru
    auth = Auth9111(bypass)
    if not auth.login(email, password):
        logger.error("❌ Не удалось авторизоваться на 9111.ru. Выход.")
        return

    logger.info("✅ Успешная авторизация на 9111.ru")

    # 4. Парсинг Telegram канала
    logger.info(f"📱 Парсинг Telegram канала: {channel_id}")
    tg_parser = TelegramRSSParser()
    
    try:
        # Используем RSS парсер (уже есть в проекте)
        posts = tg_parser.get_posts(channel_id, limit=3)
        
        if not posts:
            logger.warning("❌ Не получено постов из Telegram.")
            return
            
        logger.info(f"✅ Получено {len(posts)} постов из Telegram")
    except Exception as e:
        logger.exception(f"❌ Ошибка парсинга Telegram: {e}")
        return

    # 5. Инициализация API публикаций
    pub_api = PublicationAPI(
        session=auth.session,
        user_hash=user_hash,
        uuk=uuk
    )

    # 6. Публикация каждого поста
    successful = 0
    for i, post in enumerate(posts, 1):
        logger.info(f"--- 📝 Обработка поста {i}/{len(posts)} ---")
        
        # Извлекаем данные поста
        title = post.get("title", "")[:100]  # Первые 100 символов как заголовок
        content = post.get("content", "")
        image_url = post.get("image_url")
        
        # Скачиваем изображение, если есть
        image_path = None
        if image_url:
            image_path = utils.download_image(image_url, f"post_{i}")
        
        # Получаем ID рубрики (по умолчанию "новости")
        rubric_id = get_rubric_id("новости")
        
        # Формируем теги
        tags = "новости, закон, право"
        
        # Создаем публикацию
        logger.info(f"Заголовок: {title}")
        success = pub_api.create_publication(
            title=title,
            content=content,
            rubric_name="новости",
            tags=tags,
            image_path=image_path
        )
        
        if success:
            successful += 1
            logger.info(f"✅ Пост {i} успешно опубликован")
        else:
            logger.error(f"❌ Ошибка публикации поста {i}")
        
        # Удаляем временное изображение
        if image_path:
            utils.safe_remove_file(image_path)
        
        # Небольшая задержка между публикациями
        import time
        time.sleep(5)

    # 7. Очистка
    utils.cleanup_temp_files()
    
    logger.info("=" * 50)
    logger.info(f"📊 Итог: {successful}/{len(posts)} постов опубликовано")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
