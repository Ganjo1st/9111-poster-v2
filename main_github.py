def add_cookies_from_file(driver):
    """Добавляет куки из файла в driver и проверяет авторизацию"""
    cookies = [
        {'name': 'user_hash', 'value': Config.USER_HASH, 'domain': '.9111.ru', 'path': '/'},
        {'name': 'uuk', 'value': 'cad1a52ec9d948e6cc9ef7cae9009203', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'geo', 'value': '91-817-1', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'au', 'value': '%7B%22u%22%3A2368040%2C%22k%22%3A%22aa8ca3729252da5450cdb0862352503d%22%2C%22t%22%3A1773746119%7D', 'domain': '.9111.ru', 'path': '/'},
    ]
    
    # Сначала открываем домен, чтобы можно было добавить куки
    logger.info("🌐 Открываем главную страницу для установки кук...")
    driver.get("https://9111.ru")
    time.sleep(5)
    
    # Сохраняем скриншот главной страницы до добавления кук
    driver.save_screenshot("before_cookies.png")
    logger.info("📸 Скриншот до добавления кук сохранен")
    
    # Добавляем куки
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
            logger.info(f"✅ Добавлена кука: {cookie['name']}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось добавить куку {cookie['name']}: {e}")
    
    # Обновляем страницу
    driver.refresh()
    time.sleep(5)
    
    # Сохраняем скриншот после добавления кук
    driver.save_screenshot("after_cookies.png")
    logger.info("📸 Скриншот после добавления кук сохранен")
    
    # Проверяем текущий URL и статус
    current_url = driver.current_url
    page_title = driver.title
    logger.info(f"📍 Текущий URL: {current_url}")
    logger.info(f"📄 Заголовок страницы: {page_title}")
    
    # Проверяем, есть ли признаки авторизации
    page_source = driver.page_source
    
    # Ищем признаки успешной авторизации
    auth_indicators = [
        Config.USER_HASH,
        "user_hash",
        "Мои публикации",
        "Выход",
        "Личный кабинет",
        Config.NINTH_EMAIL.split('@')[0]  # Часть email до @
    ]
    
    authorized = False
    for indicator in auth_indicators:
        if indicator and indicator in page_source:
            logger.info(f"✅ Найден признак авторизации: {indicator[:50]}")
            authorized = True
            break
    
    if not authorized:
        logger.warning("⚠️ Признаки авторизации не найдены")
        # Сохраняем HTML для анализа
        with open("auth_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        logger.info("📄 HTML страницы сохранен в auth_page.html")
    
    # Проверяем, нет ли ошибки 403 в тексте
    if "403" in page_source or "Forbidden" in page_source:
        logger.error("❌ Обнаружена ошибка 403 Forbidden на главной странице")
        return False
    
    return authorized
