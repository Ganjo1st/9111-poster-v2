#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный публикатор для 9111.ru
Исправленная версия с правильной проверкой авторизации
"""

import os
import sys
import json
import time
import random
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Импортируем наши модули
from src.telegram_client import TelegramClient
from src.browser_manager import BrowserManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('poster.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('9111_poster')

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
NINTH_EMAIL = os.getenv('NINTH_EMAIL')
NINTH_PASSWORD = os.getenv('NINTH_PASSWORD')
STATE_FILE = Path('data') / 'posted_9111.json'
USER_ID = '2368040'  # Ваш ID пользователя для проверки авторизации

# Режим работы
GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'

# Создаем папки
Path('data').mkdir(exist_ok=True)
Path('logs').mkdir(exist_ok=True)
Path('screenshots').mkdir(exist_ok=True)
Path('downloads').mkdir(exist_ok=True)

class Poster9111:
    """Основной класс публикатора"""

    def __init__(self):
        self.telegram = TelegramClient(TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID)
        self.browser = None
        self.posted_ids = self.load_state()

        logger.info("="*60)
        logger.info("🚀 ПУБЛИКАТОР НА 9111.RU ЗАПУЩЕН")
        logger.info(f"📁 Ранее опубликовано постов: {len(self.posted_ids)}")
        logger.info(f"🌐 Режим: {'GitHub Actions' if GITHUB_ACTIONS else 'Локальный'}")
        logger.info("="*60)

    def load_state(self) -> set:
        """Загружает список опубликованных постов"""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        logger.info(f"✅ Загружено {len(data)} записей из файла состояния")
                        return set(data)
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки состояния: {e}")
        return set()

    def save_state(self):
        """Сохраняет список опубликованных постов"""
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.posted_ids), f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Сохранено {len(self.posted_ids)} записей в файл состояния")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")

    def clean_text(self, text: str) -> tuple:
        """Очищает текст, выделяет заголовок и контент"""
        if not text:
            return "", ""

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return "", ""

        title = lines[0][:150]  # Ограничиваем длину заголовка
        content = '\n'.join(lines[1:]) if len(lines) > 1 else lines[0]

        return title, content

    def get_new_posts(self) -> List[Dict]:
        """Получает новые посты из Telegram"""
        posts = self.telegram.get_channel_posts(limit=10)

        if not posts:
            return []

        new_posts = []
        for p in posts:
            if p['id'] not in self.posted_ids:
                # Проверяем дату (не старше 7 дней)
                post_date = datetime.fromtimestamp(p.get('date', 0))
                if datetime.now() - post_date < timedelta(days=7):
                    new_posts.append(p)

        if new_posts:
            logger.info(f"🆕 Найдено новых постов: {len(new_posts)}")
        else:
            logger.info("📭 Новых постов нет")

        return new_posts[:5]  # Максимум 5 постов за раз

    def run(self):
        """Основной цикл работы"""
        try:
            # Получаем новые посты
            new_posts = self.get_new_posts()
            if not new_posts:
                logger.info("✨ Нет новых постов для публикации")
                return

            # Запускаем браузер
            self.browser = BrowserManager(
                email=NINTH_EMAIL,
                password=NINTH_PASSWORD,
                user_id=USER_ID,
                headless=GITHUB_ACTIONS
            )

            if not self.browser.start():
                logger.error("❌ Не удалось запустить браузер")
                return

            # Выполняем вход
            if not self.browser.login():
                logger.error("❌ Не удалось войти на сайт")
                return

            # Публикуем посты
            published = 0
            for i, post in enumerate(new_posts, 1):
                logger.info(f"\n📄 Пост {i}/{len(new_posts)} (ID: {post['id']})")

                title, content = self.clean_text(post['text'])
                if not title:
                    logger.warning(f"⚠️ Пост {post['id']} пустой, пропускаем")
                    self.posted_ids.add(post['id'])
                    continue

                # Скачиваем фото если есть
                photo_path = None
                if post.get('has_photo') and post.get('photo'):
                    photo_path = self.telegram.download_photo(post['photo'], post['id'])

                logger.info(f"📌 Заголовок: {title[:70]}...")

                if self.browser.publish_post(title, content, photo_path):
                    self.posted_ids.add(post['id'])
                    published += 1
                    self.save_state()

                # Удаляем временное фото
                if photo_path and os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                        logger.info(f"🗑️ Временное фото удалено: {photo_path}")
                    except:
                        pass

                # Пауза между постами (от 1 до 3 минут)
                if i < len(new_posts):
                    delay = random.randint(60, 180)
                    logger.info(f"⏳ Ожидание {delay} секунд перед следующим постом...")
                    time.sleep(delay)

            logger.info(f"\n📊 ИТОГИ: Опубликовано {published} из {len(new_posts)} постов")

        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            if self.browser:
                self.browser.save_screenshot('critical_error.png')
        finally:
            if self.browser:
                self.browser.stop()

def main():
    """Точка входа"""
    if not all([TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID, NINTH_EMAIL, NINTH_PASSWORD]):
        logger.error("❌ Не все переменные окружения заданы!")
        logger.info("📁 Проверьте файл .env или настройки Secrets в GitHub")
        logger.info("   Нужны: TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID, NINTH_EMAIL, NINTH_PASSWORD")
        sys.exit(1)

    poster = Poster9111()
    poster.run()

if __name__ == "__main__":
    main()
