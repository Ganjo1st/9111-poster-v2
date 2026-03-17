import os
import sys
import requests
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

import modules.telegram_bot_parser as tg_module
from modules.config import Config
from modules.logger import setup_logging
from modules.publication_api import PublicationAPI
from modules.rubric_mapper import get_rubric_id

# Настройка логирования
logger = setup_logging()


def create_session_from_secrets():
    """Создает сессию напрямую из секретов USER_HASH и UUK"""
    
    logger.info("🔄 Создаем сессию из секретов")
    
    user_hash = Config.USER_HASH
    uuk = Config.UUK
    
    if not user_hash or not uuk:
        logger.error("❌ USER_HASH или UUK не заданы")
        return None
    
    logger.info(f"✅ USER_HASH: {user_hash[:10]}...")
    logger.info(f"✅ UUK: {uuk[:10]}...")
    
    session = requests.Session()
    
    # Устанавливаем куки
    session.cookies.set('user_hash', user_hash, domain='.9111.ru')
    session.cookies.set('uuk', uuk, domain='.9111.ru')
    
    # Заголовки
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    
    return session


def get_telegram_posts():
    """Получает посты из Telegram"""
    logger.info("🤖 Получаем посты из Telegram...")
    
    if not hasattr(tg_module, 'TelegramBotParser'):
        logger.error("❌ Класс TelegramBotParser не найден")
        return []
    
    ParserClass = tg_module.TelegramBotParser
    
    try:
        parser = ParserClass(Config.TELEGRAM_TOKEN, Config.CHANNEL_ID)
        logger.info("✅ Парсер создан")
        
        if hasattr(parser, 'parse_channel_posts'):
            raw_posts = parser.parse_channel_posts()
            
            if raw_posts:
                logger.info(f"📦 Получено {len(raw_posts)} постов")
                
                # Преобразуем в нужный формат
                posts = []
                for raw in raw_posts:
                    if isinstance(raw, dict):
                        post = {
                            'title': raw.get('text', '')[:100],
                            'content': raw.get('text', ''),
                        }
                        if post['content']:
                            posts.append(post)
                
                logger.info(f"✅ Преобразовано {len(posts)} постов")
                return posts
            
        return []
        
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        return []


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster")
    logger.info("=" * 50)

    # 1. Создаем сессию
    session = create_session_from_secrets()
    if not session:
        logger.error("❌ Не удалось создать сессию")
        return

    # 2. Получаем посты
    posts = get_telegram_posts()
    if not posts:
        logger.warning("❌ Нет постов")
        return

    logger.info(f"✅ Получено {len(posts)} постов")

    # 3. Публикуем
    pub_api = PublicationAPI(
        session=session,
        user_hash=Config.USER_HASH,
        uuk=Config.UUK
    )

    successful = 0
    for i, post in enumerate(posts, 1):
        logger.info(f"--- 📝 Пост {i}/{len(posts)} ---")
        
        title = post.get("title", "").strip()
        content = post.get("content", "").strip()
        
        if not content:
            logger.warning(f"⚠️ Пост {i} пустой")
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
            logger.error(f"❌ Ошибка поста {i}")

    logger.info(f"📊 Итог: {successful}/{len(posts)}")


if __name__ == "__main__":
    main()
