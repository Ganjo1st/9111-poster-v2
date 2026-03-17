#!/usr/bin/env python3
"""
9111.ru Poster - Автоматическая публикация из Telegram
Запускается как GitHub Action
"""

import os
import sys
import time
import json
import logging
import random
from datetime import datetime
from pathlib import Path

# Добавляем пути для импортов
sys.path.insert(0, str(Path(__file__).parent))

from modules.auth import Auth9111
from modules.bypass import BypassManager
from modules.telegram_bot import TelegramBot
from modules.publication_github import PublicationManager
from modules.logger import setup_logging, log_function_call
from modules.utils import cleanup_temp_files

# Настройка логирования
logger = setup_logging()


class Poster9111:
    """Основной класс приложения"""
    
    def __init__(self):
        self.env = self._load_env()
        self.bypass = None
        self.auth = None
        self.telegram = None
        
    def _load_env(self):
        """Загрузка переменных окружения"""
        required = ['NINTH_EMAIL', 'NINTH_PASSWORD', 'TELEGRAM_TOKEN', 'CHANNEL_ID']
        env = {}
        
        for key in required:
            value = os.getenv(key)
            if not value:
                raise ValueError(f"Отсутствует обязательная переменная: {key}")
            env[key] = value
            
        # Опциональные переменные
        env['USER_HASH'] = os.getenv('USER_HASH', '')
        env['UUK'] = os.getenv('UUK', '')
        
        return env
    
    @log_function_call
    def run(self):
        """Основной метод выполнения"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("🚀 Запуск 9111 Poster в GitHub Actions")
        logger.info(f"📅 Время: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        try:
            # 1. Инициализация
            self.bypass = BypassManager()
            
            # 2. Авторизация на 9111.ru
            logger.info("🔐 Авторизация на 9111.ru...")
            self.auth = Auth9111(self.bypass)
            
            auth_success = self.auth.login(
                self.env['NINTH_EMAIL'], 
                self.env['NINTH_PASSWORD']
            )
            
            if not auth_success:
                logger.error("❌ Не удалось авторизоваться на 9111.ru")
                return False
                
            logger.info("✅ Успешная авторизация")
            
            # 3. Получение постов из Telegram
            logger.info("📱 Получение постов из Telegram...")
            self.telegram = TelegramBot(self.env['TELEGRAM_TOKEN'])
            
            posts = self.telegram.get_channel_posts(
                channel_id=self.env['CHANNEL_ID'],
                limit=3  # По 3 поста за запуск
            )
            
            if not posts:
                logger.warning("⚠️ Нет новых постов в Telegram")
                return True
                
            logger.info(f"📦 Получено {len(posts)} постов")
            
            # 4. Публикация каждого поста
            logger.info("📤 Начало публикации...")
            
            # Создаем менеджер публикаций
            pub_manager = PublicationManager(
                auth_session=self.auth,
                bypass=self.bypass,
                user_hash=self.env['USER_HASH'],
                uuk=self.env['UUK']
            )
            
            success_count = 0
            for i, post in enumerate(posts, 1):
                logger.info(f"--- Пост {i}/{len(posts)} ---")
                
                result = pub_manager.publish_post(
                    title=post['title'],
                    content=post['content'],
                    image_url=post.get('image_url'),
                    tags=post.get('tags', 'новости, актуально')
                )
                
                if result:
                    success_count += 1
                    logger.info(f"✅ Пост {i} опубликован")
                else:
                    logger.error(f"❌ Ошибка публикации поста {i}")
                
                # Пауза между постами
                if i < len(posts):
                    time.sleep(random.randint(10, 20))
            
            # 5. Итоги
            elapsed = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"📊 Итоги выполнения:")
            logger.info(f"   ✅ Успешно: {success_count}/{len(posts)}")
            logger.info(f"   ⏱️ Время: {elapsed:.1f} сек")
            logger.info("=" * 60)
            
            return success_count > 0
            
        except Exception as e:
            logger.exception(f"💥 Критическая ошибка: {e}")
            return False
            
        finally:
            # Очистка временных файлов
            cleanup_temp_files()
            logger.info("🧹 Временные файлы очищены")


if __name__ == "__main__":
    poster = Poster9111()
    success = poster.run()
    sys.exit(0 if success else 1)
