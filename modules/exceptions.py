"""
Кастомные исключения для проекта 9111-poster
"""

class Base9111Error(Exception):
    """Базовое исключение для проекта."""
    pass


class AuthError(Base9111Error):
    """Ошибка авторизации на сайте."""
    pass


class PublicationError(Base9111Error):
    """Ошибка при создании публикации."""
    pass


class TelegramParseError(Base9111Error):
    """Ошибка при парсинге Telegram."""
    pass
