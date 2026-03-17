def add_cookies_from_file(driver, target_url):
    """Добавляет куки после перехода на целевой URL"""
    cookies = [
        {'name': 'user_hash', 'value': '268b9697896aefb3e62b2a209b9cafc6', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'geo', 'value': '91-817-1', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'uuk', 'value': 'cad1a52ec9d948e6cc9ef7cae9009203', 'domain': '.9111.ru', 'path': '/'},
        {'name': 'au', 'value': '%7B%22u%22%3A2368040%2C%22k%22%3A%22aa8ca3729252da5450cdb0862352503d%22%2C%22t%22%3A1773748465%7D', 'domain': '.9111.ru', 'path': '/'},
    ]
    
    logger.info("=" * 50)
    logger.info(f"🌐 Переходим на {target_url}")
    driver.get(target_url)
    time.sleep(5)
    
    driver.save_screenshot("before_cookies.png")
    logger.info("📸 Скриншот до добавления кук: before_cookies.png")
    
    logger.info("=" * 50)
    logger.info("🍪 Добавляем куки...")
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
            logger.info(f"✅ Добавлена кука: {cookie['name']}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось добавить куку {cookie['name']}: {e}")
    
    logger.info("=" * 50)
    logger.info("🔄 Обновляем страницу...")
    driver.refresh()
    time.sleep(5)
    
    driver.save_screenshot("after_cookies.png")
    logger.info("📸 Скриншот после добавления кук: after_cookies.png")
    
    current_url = driver.current_url
    page_title = driver.title
    logger.info(f"📍 Текущий URL: {current_url}")
    logger.info(f"📄 Заголовок страницы: {page_title}")
    
    try:
        form = driver.find_element(By.ID, "form_create_topic_group")
        logger.info("✅ ФОРМА НАЙДЕНА! Авторизация успешна")
        return True
    except:
        logger.error("❌ Форма не найдена")
        with open("error_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("📄 HTML страницы сохранен: error_page.html")
        return False
