def create_session_from_secrets():
    """Создает сессию из полного набора кук"""
    
    logger.info("🔄 Создаем сессию с полным набором кук")
    
    user_hash = Config.USER_HASH
    uuk = "cad1a52ec9d948e6cc9ef7cae9009203"  # Новое значение из файла!
    
    if not user_hash:
        logger.error("❌ USER_HASH не задан")
        return None
    
    logger.info(f"✅ USER_HASH: {user_hash[:10]}...")
    logger.info(f"✅ UUK: {uuk[:10]}...")
    
    session = requests.Session()
    
    # Устанавливаем ВСЕ куки как в браузере
    cookies = [
        {'name': 'user_hash', 'value': user_hash, 'domain': '.9111.ru', 'path': '/'},
        {'name': 'uuk', 'value': uuk, 'domain': '.9111.ru', 'path': '/'},
        {'name': 'geo', 'value': '91-817-1', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'au', 'value': '%7B%22u%22%3A2368040%2C%22k%22%3A%22aa8ca3729252da5450cdb0862352503d%22%2C%22t%22%3A1773746119%7D', 'domain': '.9111.ru', 'path': '/'},
    ]
    
    for cookie in cookies:
        session.cookies.set(
            cookie['name'], 
            cookie['value'],
            domain=cookie['domain'],
            path=cookie['path']
        )
    
    # Заголовки как в браузере
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    
    # Выводим установленные куки для проверки
    cookies_dict = session.cookies.get_dict()
    logger.info(f"🍪 Установлены куки: {list(cookies_dict.keys())}")
    
    return session
