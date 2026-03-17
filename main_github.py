#!/usr/bin/env python3
"""
Основной скрипт для GitHub Actions.
Получает посты из Telegram и публикует их на 9111.ru.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from modules.logger import setup_logging
from modules.github_actions_auth import GitHubActionsAuth
from modules.telegram_bot_parser import TelegramBotParser
from modules.publication import PublicationManager
from modules.exceptions import PublicationError
from modules import utils

# Настройка логирования
logger = setup_logging(log_file="logs/github_poster.log")


def get_env_var(name: str, required: bool = True) -> str:
    """Получает переменную окружения."""
    value = os.getenv(name)
    if required and not value:
        raise ValueError(f"❌ Переменная окружения {name} не установлена")
    return value


def main():
    """Основная функция."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("🚀 Запуск 9111 Poster в GitHub Actions")
    logger.info("=" * 60)
    
    try:
        # 1. Получаем переменные окружения
        logger.info("📦 Загрузка конфигурации...")
        
        # 9111 credentials
        email = get_env_var("NINTH_EMAIL")
        password = get_env_var("NINTH_PASSWORD")
        user_hash = get_env_var("USER_HASH", required=False)
        uuk = get_env_var("UUK", required=False)
        
        # Telegram
        telegram_token = get_env_var("TELEGRAM_TOKEN")
        channel_id = get_env_var("CHANNEL_ID")
        
        # Settings
        rubric_id = int(get_env_var("PUBLICATION_RUBRIC_ID", required=False) or "382235")
        default_tags = get_env_var("PUBLICATION_TAGS", required=False) or "новости, закон, право"
        max_posts = int(get_env_var("MAX_POSTS_PER_RUN", required=False) or "3")
        
        logger.info(f"📰 Канал: {channel_id}")
        logger.info(f"🏷️  Рубрика ID: {rubric_id}")
        logger.info(f"🔖 Теги: {default_tags}")
        logger.info(f"📊 Макс. постов: {max_posts}")
        
        # 2. Авторизация на 9111.ru
        logger.info("🔑 Авторизация на 9111.ru...")
        auth = GitHubActionsAuth(email, password, user_hash, uuk)
        
        if not auth.ensure_login():
            logger.error("❌ Не удалось авторизоваться на 9111.ru")
            return 1
            
        logger.info("✅ Успешная авторизация")
        
        # 3. Парсинг Telegram канала
        logger.info("📱 Парсинг Telegram канала...")
        tg_parser = TelegramBotParser(telegram_token, channel_id)
        posts = tg_parser.parse_channel_posts(limit=max_posts)
        
        if not posts:
            logger.warning("⚠️ Нет новых постов в Telegram")
            return 0
            
        logger.info(f"✅ Получено {len(posts)} постов")
        
        # 4. Публикация постов
        logger.info("📝 Начинаем публикацию...")
        driver = auth.get_driver()
        pub_manager = PublicationManager(driver, rubric_id, default_tags)
        
        successful = 0
        failed = 0
        
        for i, post in enumerate(posts, 1):
            logger.info(f"\n--- Пост {i}/{len(posts)} ---")
            logger.info(f"📄 Текст: {post['text'][:100]}...")
            logger.info(f"🖼️  Фото: {'есть' if post['photo_path'] else 'нет'}")
            
            # Формируем заголовок (первые 100 символов или до точки)
            title = post['text'].split('\n')[0][:150]  # Первая строка
            if len(title) < 10:  # Если заголовок слишком короткий
                title = post['text'][:150]
                
            # Очищаем заголовок от лишних символов
            title = title.strip() or "Новость из Telegram"
            
            try:
                success = pub_manager.create_publication(
                    title=title,
                    content=post['text'],
                    tags=default_tags,
                    image_path=post['photo_path']
                )
                
                if success:
                    successful += 1
                    logger.info(f"✅ Пост {i} опубликован")
                else:
                    failed += 1
                    logger.error(f"❌ Пост {i} не опубликован")
                    
            except Exception as e:
                failed += 1
                logger.exception(f"❌ Критическая ошибка при публикации поста {i}: {e}")
                
            # Пауза между постами
            if i < len(posts):
                time.sleep(10)
        
        # 5. Итоги
        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"📊 ИТОГИ ЗАПУСКА")
        logger.info(f"✅ Успешно: {successful}")
        logger.info(f"❌ Ошибок: {failed}")
        logger.info(f"⏱️ Время: {elapsed_time:.2f} сек")
        logger.info("=" * 60)
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")
        return 1
        
    finally:
        # Очистка
        if 'auth' in locals():
            auth.close()
        utils.cleanup_temp_files()
        logger.info("🧹 Очистка завершена")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
