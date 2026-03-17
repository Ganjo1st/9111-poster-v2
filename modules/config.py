import os

class Config:
    # 9111
    NINTH_EMAIL = os.getenv("NINTH_EMAIL")
    NINTH_PASSWORD = os.getenv("NINTH_PASSWORD")
    USER_HASH = os.getenv("USER_HASH")
    UUK = os.getenv("UUK")  # Это будет переопределено в коде

    # Telegram
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Настройки публикации
    DEFAULT_RUBRIC = os.getenv("DEFAULT_RUBRIC", "новости")
    DEFAULT_TAGS = os.getenv("DEFAULT_TAGS", "новости, закон, право")
    POSTS_LIMIT = int(os.getenv("POSTS_LIMIT", 3))
