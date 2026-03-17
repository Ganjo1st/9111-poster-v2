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


def create_session_from_auth(auth):
    """Создает сессию используя user_hash и uuk"""
    import requests
    
    logger.info("🔄 Создаем сессию из user_hash и uuk")
    
    # Безопасно получаем user_hash и uuk
    user_hash = safe_get_attr(auth, 'user_hash')
    uuk = safe_get_attr(auth, 'uuk')
    
    if user_hash:
        logger.info(f"✅ Найден user_hash в auth: {user_hash[:10]}...")
    else:
        logger.warning("⚠️ user_hash не найден в auth")
        user_hash = Config.USER_HASH
        if user_hash:
            logger.info(f"✅ Используем user_hash из Config: {user_hash[:10]}...")
    
    if uuk:
        logger.info(f"✅ Найден uuk в auth: {uuk[:10]}...")
    else:
        logger.warning("⚠️ uuk не найден в auth")
        uuk = Config.UUK
        if uuk:
            logger.info(f"✅ Используем uuk из Config: {uuk[:10]}...")
    
    if not user_hash or not uuk:
        logger.error("❌ Нет user_hash или uuk")
        return None
    
    # Создаем сессию
    session = requests.Session()
    
    # Добавляем стандартные headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Пытаемся установить cookies с user_hash и uuk
    session.cookies.set('user_hash', user_hash, domain='.9111.ru')
    session.cookies.set('uuk', uuk, domain='.9111.ru')
    
    # Проверяем сессию
    try:
        test_response = session.get('https://9111.ru', allow_redirects=True, timeout=10)
        logger.info(f"🌐 Тестовый запрос вернул статус: {test_response.status_code}")
        
        if test_response.status_code == 200:
            logger.info("✅ Сессия успешно создана")
            return session
        else:
            logger.warning(f"⚠️ Сессия вернула статус {test_response.status_code}")
            
            # Пробуем добавить куки из cookies_file если есть
            cookies_path = safe_get_attr(auth, 'cookies_file', 'sessions/cookies.pkl')
            if os.path.exists(cookies_path):
                try:
                    with open(cookies_path, 'rb') as f:
                        cookies = pickle.load(f)
                    for cookie in cookies:
                        session.cookies.set(cookie['name'], cookie['value'])
                    logger.info("✅ Добавлены cookies из файла")
                    
                    # Проверяем снова
                    test_response = session.get('https://9111.ru', allow_redirects=True, timeout=10)
                    if test_response.status_code == 200:
                        logger.info("✅ Сессия работает после добавления cookies")
                        return session
                except Exception as e:
                    logger.warning(f"Не удалось загрузить cookies: {e}")
            
            return session  # Все равно возвращаем
    except Exception as e:
        logger.warning(f"Ошибка при проверке сессии: {e}")
        return session  # Возвращаем даже если проверка не удалась


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
                    # Выводим информацию о первом посте
                    if len(posts) > 0:
                        first_post = posts[0]
                        title = first_post.get('title', '')[:50]
                        logger.info(f"📄 Первый пост: {title}...")
                    return posts
                else:
                    logger.warning("parse_channel_posts() вернул пустой список")
            except Exception as e:
                logger.warning(f"Ошибка в parse_channel_posts(): {e}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании парсера: {e}")
    
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
            logger.info("🔐 Выполняем login...")
            login_result = auth.login()
            if not login_result:
                logger.error("❌ Ошибка авторизации")
                return
            logger.info("✅ Login выполнен успешно")
        
        # Безопасно проверяем атрибуты
        user_hash = safe_get_attr(auth, 'user_hash')
        uuk = safe_get_attr(auth, 'uuk')
        
        if user_hash:
            logger.info(f"✅ user_hash найден: {user_hash[:10]}...")
        else:
            logger.warning("⚠️ user_hash отсутствует в auth, используем из Config")
            
        if uuk:
            logger.info(f"✅ uuk найден: {uuk[:10]}...")
        else:
            logger.warning("⚠️ uuk отсутствует в auth, используем из Config")
        
        logger.info("✅ Авторизация выполнена")
        
        # Создаем сессию
        session = create_session_from_auth(auth)
        
        if session is None:
            logger.error("❌ Не удалось создать сессию")
            return
            
        logger.info("✅ Сессия создана успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        pub_api = PublicationAPI(
            session=session,
            user_hash=Config.USER_HASH,  # Всегда используем из Config
            uuk=Config.UUK                # Всегда используем из Config
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
