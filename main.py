import os
import sys
import pickle
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


def safe_get_attr(obj, attr_name, default=None):
    """Безопасно получает атрибут объекта"""
    if hasattr(obj, attr_name):
        value = getattr(obj, attr_name)
        if value is not None:
            return value
    return default


def create_session_from_secrets():
    """Создает сессию напрямую из секретов USER_HASH и UUK"""
    import requests
    
    logger.info("🔄 Создаем сессию из секретов USER_HASH и UUK")
    
    user_hash = Config.USER_HASH
    uuk = Config.UUK
    
    if not user_hash or not uuk:
        logger.error("❌ USER_HASH или UUK не заданы в секретах")
        return None
    
    logger.info(f"✅ USER_HASH: {user_hash[:10]}...")
    logger.info(f"✅ UUK: {uuk[:10]}...")
    
    session = requests.Session()
    
    # Добавляем cookies
    session.cookies.set('user_hash', user_hash, domain='.9111.ru')
    session.cookies.set('uuk', uuk, domain='.9111.ru')
    
    # Добавляем стандартные headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Проверяем сессию
    try:
        test_response = session.get('https://9111.ru', allow_redirects=True, timeout=10)
        logger.info(f"🌐 Тестовый запрос вернул статус: {test_response.status_code}")
        
        if test_response.status_code == 200:
            logger.info("✅ Сессия успешно создана из секретов")
            return session
        else:
            logger.warning(f"⚠️ Сессия вернула статус {test_response.status_code}")
            return session  # Все равно возвращаем
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при проверке сессии: {e}")
        return session  # Возвращаем даже если проверка не удалась


def get_telegram_posts():
    """Получает посты из Telegram и преобразует в нужный формат"""
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
                raw_posts = parser.parse_channel_posts()
                
                # Выводим информацию о сырых данных для отладки
                logger.info(f"📦 Тип полученных данных: {type(raw_posts)}")
                
                if raw_posts:
                    logger.info(f"📦 Количество: {len(raw_posts)}")
                    
                    # Показываем первый пост в сыром виде
                    if len(raw_posts) > 0:
                        first_raw = raw_posts[0]
                        logger.info(f"📄 Сырой первый пост (тип: {type(first_raw)}):")
                        
                        # Если это словарь, показываем ключи
                        if isinstance(first_raw, dict):
                            logger.info(f"    Ключи: {list(first_raw.keys())}")
                            # Пробуем найти текст
                            for key in ['text', 'message', 'content', 'caption', 'title']:
                                if key in first_raw and first_raw[key]:
                                    logger.info(f"    {key}: {first_raw[key][:100]}...")
                        else:
                            # Если это не словарь, показываем само значение
                            logger.info(f"    Значение: {str(first_raw)[:200]}")
                    
                    # Преобразуем в единый формат
                    posts = []
                    for raw_post in raw_posts:
                        post = {}
                        
                        # Пробуем разные варианты полей
                        if isinstance(raw_post, dict):
                            # Пробуем найти заголовок
                            for title_key in ['title', 'header', 'subject', 'caption']:
                                if title_key in raw_post and raw_post[title_key]:
                                    post['title'] = str(raw_post[title_key])
                                    break
                            
                            # Пробуем найти контент
                            for content_key in ['text', 'content', 'message', 'body', 'caption']:
                                if content_key in raw_post and raw_post[content_key]:
                                    post['content'] = str(raw_post[content_key])
                                    break
                            
                            # Копируем остальные поля
                            for key, value in raw_post.items():
                                if key not in ['title', 'content']:
                                    post[key] = value
                        else:
                            # Если это не словарь, используем как контент
                            post['content'] = str(raw_post)
                            post['title'] = str(raw_post)[:100]
                        
                        # Если нет заголовка, берем первые 100 символов контента
                        if not post.get('title') and post.get('content'):
                            post['title'] = post['content'][:100]
                        
                        # Если нет контента, пропускаем
                        if post.get('content'):
                            posts.append(post)
                    
                    logger.info(f"✅ Преобразовано {len(posts)} постов")
                    
                    # Показываем первый преобразованный пост
                    if posts and len(posts) > 0:
                        first_post = posts[0]
                        logger.info(f"📄 Преобразованный первый пост:")
                        logger.info(f"    Заголовок: {first_post.get('title', '')[:100]}")
                        logger.info(f"    Контент: {first_post.get('content', '')[:100]}...")
                    
                    return posts
                else:
                    logger.warning("parse_channel_posts() вернул пустой список")
                    return []
                    
            except Exception as e:
                logger.warning(f"Ошибка в parse_channel_posts(): {e}")
                import traceback
                logger.warning(traceback.format_exc())
                return []
        
        return []
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании парсера: {e}")
        return []


def main():
    logger.info("=" * 50)
    logger.info("🚀 Запуск 9111 Poster")
    logger.info("=" * 50)

    # 1. Создаем сессию напрямую из секретов
    session = create_session_from_secrets()
    
    if session is None:
        logger.error("❌ Не удалось создать сессию из секретов")
        return
    
    logger.info("✅ Сессия создана успешно")

    # 2. Парсинг Telegram
    posts = get_telegram_posts()

    if not posts:
        logger.warning("❌ Нет постов для публикации")
        return

    logger.info(f"✅ Получено {len(posts)} постов")

    # 3. Публикация
    try:
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
            
            # Если нет контента, пробуем взять из других полей
            if not content:
                for field in ['text', 'message', 'body']:
                    if field in post and post[field]:
                        content = str(post[field]).strip()
                        break
            
            # Если нет заголовка, берем из контента
            if not title and content:
                title = content[:100]
            
            if not title or not content:
                logger.warning(f"⚠️ Пост {i} пропущен: нет заголовка или контента")
                logger.warning(f"   Доступные поля: {list(post.keys())}")
                continue
                
            logger.info(f"Заголовок: {title}")
            logger.info(f"Контент: {content[:100]}...")
            
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
