def update_proxy(self, proxies: dict):
    """
    Обновляет прокси в существующей сессии.
    
    Args:
        proxies: Новый словарь прокси
    """
    if proxies:
        self.proxies = proxies
        self.session.proxies.update(proxies)
        logger.info(f"🔌 Прокси обновлены: {proxies}")
        
        # Проверяем, что сессия все еще работает
        try:
            test_response = self.session.get(self.PROFILE_URL, timeout=10)
            if test_response.status_code == 200:
                logger.info("✅ Сессия с новым прокси работает")
                return True
            else:
                logger.warning("⚠️ Сессия с новым прокси не работает")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке сессии: {e}")
            return False
    return False
