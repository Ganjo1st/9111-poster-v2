import logging
import sys
from functools import wraps
from typing import Any, Callable


def setup_logging(level=logging.INFO) -> logging.Logger:
    """Настройка логирования для проекта."""
    logger = logging.getLogger("9111_poster")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_function_call(func: Callable) -> Callable:
    """Декоратор для логирования вызовов функций."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("9111_poster")
        logger.debug(f"Вызов {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Завершен {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Ошибка в {func.__name__}: {e}")
            raise
    return wrapper
