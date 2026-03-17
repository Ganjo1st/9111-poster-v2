import os
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

logger = logging.getLogger(__name__)

class TelegramParser:
    """Парсер постов из Telegram канала"""
    
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID', '29654723')
        self.api_hash = os.getenv('TELEGRAM_API_HASH', 'fb8d32af0d38ef9e6817e02acb83f087')
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.channel = os.getenv('CHANNEL_ID', '@Novikon_news')
        self.client = None
        
    async def async_get_posts(self, limit=10):
        """Асинхронное получение постов"""
        if not self.client:
            self.client = TelegramClient('session_name', self.api_id, self.api_hash)
            await self.client.start(bot_token=self.token)
            
        posts = []
        try:
            async for message in self.client.iter_messages(self.channel, limit=limit):
                if message.text:
                    posts.append({
                        'id': message.id,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'text': message.text,
                        'has_media': bool(message.media)
                    })
        except Exception as e:
            logger.error(f"Ошибка при получении постов: {e}")
        finally:
            await self.client.disconnect()
            
        return posts
        
    def get_channel_posts(self, limit=10):
        """Синхронная обертка для получения постов"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_get_posts(limit))
        finally:
            loop.close()
