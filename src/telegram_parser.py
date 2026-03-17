import os
import logging
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

logger = logging.getLogger(__name__)

class TelegramParser:
    """Парсер постов из Telegram канала"""
    
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID', '29654723')
        self.api_hash = os.getenv('TELEGRAM_API_HASH', 'fb8d32af0d38ef9e6817e02acb83f087')
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.channel = os.getenv('CHANNEL_ID', '@Novikon_news')
        self.client = None
        
        logger.info(f"📱 TelegramParser инициализирован для канала {self.channel}")
        
    async def async_get_posts(self, limit=10):
        """Асинхронное получение постов"""
        logger.info(f"📡 Получение {limit} последних постов из {self.channel}...")
        
        if not self.token:
            logger.error("❌ TELEGRAM_TOKEN не задан")
            return []
            
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)
        
        posts = []
        try:
            await self.client.start(bot_token=self.token)
            logger.info("✅ Подключение к Telegram установлено")
            
            async for message in self.client.iter_messages(self.channel, limit=limit):
                if message.text:
                    posts.append({
                        'id': message.id,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'text': message.text,
                        'has_media': bool(message.media)
                    })
                    logger.debug(f"Найден пост {message.id}: {message.text[:50]}...")
            
            logger.info(f"✅ Получено {len(posts)} постов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении постов: {e}")
        finally:
            await self.client.disconnect()
            
        return posts
        
    def get_channel_posts(self, limit=10):
        """Синхронная обертка для получения постов"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.async_get_posts(limit))
        except Exception as e:
            logger.error(f"❌ Ошибка в get_channel_posts: {e}")
            return []
        finally:
            loop.close()
