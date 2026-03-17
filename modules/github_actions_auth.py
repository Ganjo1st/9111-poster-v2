def is_authenticated(self) -> bool:
    """Проверяет, авторизована ли сессия."""
    try:
        # Пробуем зайти на страницу профиля
        response = self.session.get(self.PROFILE_URL, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            page_text = response.text.lower()
            
            # Ищем явные признаки авторизации
            auth_indicators = [
                'личный кабинет',
                'выйти',
                'logout',
                'профиль',
                'мои публикации',
                f'user_hash={self.session.cookies.get("user_hash")}' if self.session.cookies.get("user_hash") else ''
            ]
            
            for indicator in auth_indicators:
                if indicator and indicator in page_text:
                    logger.debug(f"Найден признак авторизации: {indicator}")
                    return True
            
            # Если есть куки user_hash и uuk, вероятно авторизованы
            if self.session.cookies.get('user_hash') and self.session.cookies.get('uuk'):
                logger.debug("Есть куки user_hash и uuk, считаем авторизованными")
                return True
                
        logger.debug(f"Статус ответа: {response.status_code}")
        return False
        
    except Exception as e:
        logger.debug(f"Ошибка при проверке авторизации: {e}")
        return False
