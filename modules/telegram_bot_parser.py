import logging
import requests
from typing import List, Dict, Optional
import tempfile
from pathlib import Path

from modules.exceptions import TelegramParseError
from modules.logger import log_function_call

logger = logging.getLogger(__name__)


class TelegramBotParser:
    """
    Парсер Telegram канала через Bot API.
    Проще и надежнее, чем telethon, идеально для GitHub Actions.
    """
    
    def __init__(self, bot_token: str, channel_id: str):
        """
        :param bot_token: Токен бота от @BotFather
        :param channel_id: ID канала (например, @channel или -1001234567890)
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    def _make_request(self, method: str, params: dict = None) -> dict:
        """Совершает запрос к Telegram API."""
        url = f"{self.base_url}/{method}"
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise TelegramParseError(f"Telegram API error: {data.get('description')}")
            return data
        except Exception as e:
            logger.error(f"Ошибка запроса к Telegram API: {e}")
            raise TelegramParseError(f"Failed to call Telegram API: {e}")
    
    @log_function_call
    def get_updates(self, limit: int = 10, offset: int = None) -> List[Dict]:
        """Получает последние сообщения."""
        params = {
            "timeout": 30,
            "limit": limit,
            "allowed_updates": ["message", "channel_post"]
        }
        if offset:
            params["offset"] = offset
            
        data = self._make_request("getUpdates", params)
        return data.get("result", [])
    
    @log_function_call
    def parse_channel_posts(self, limit: int = 5) -> List[Dict]:
        """
        Парсит последние посты из канала.
        Возвращает список словарей с текстом и фото.
        """
        posts = []
        updates = self.get_updates(limit=limit * 2)  # Запрашиваем с запасом
        
        temp_dir = Path("temp_media")
        temp_dir.mkdir(exist_ok=True)
        
        for update in updates:
            # Определяем тип сообщения (канал или обычный чат)
            message = update.get("channel_post") or update.get("message")
            if not message:
                continue
                
            # Проверяем, что сообщение из нужного канала
            chat = message.get("chat")
            if not chat:
                continue
                
            chat_id = str(chat.get("id"))
            chat_username = chat.get("username", "")
            
            # Проверяем соответствие channel_id
            target_id = self.channel_id.replace("@", "")
            if target_id not in chat_id and target_id not in chat_username:
                continue
            
            post_data = {
                "text": message.get("text") or message.get("caption") or "",
                "photo_path": None,
                "message_id": message.get("message_id"),
                "date": message.get("date")
            }
            
            # Проверяем наличие фото
            if "photo" in message:
                # Получаем самое большое фото
                photos = message["photo"]
                if photos:
                    # Берем последнее (самое большое)
                    file_id = photos[-1]["file_id"]
                    photo_path = self._download_photo(file_id, temp_dir / f"photo_{post_data['message_id']}.jpg")
                    if photo_path:
                        post_data["photo_path"] = str(photo_path)
                        
            # Проверяем наличие документа (может быть фото)
            elif "document" in message:
                doc = message["document"]
                mime_type = doc.get("mime_type", "")
                if mime_type.startswith("image/"):
                    file_id = doc["file_id"]
                    photo_path = self._download_photo(file_id, temp_dir / f"doc_{post_data['message_id']}.jpg")
                    if photo_path:
                        post_data["photo_path"] = str(photo_path)
            
            if post_data["text"] or post_data["photo_path"]:
                posts.append(post_data)
                
            if len(posts) >= limit:
                break
                
        logger.info(f"Найдено {len(posts)} постов в канале")
        return posts
    
    def _download_photo(self, file_id: str, save_path: Path) -> Optional[Path]:
        """Скачивает фото по file_id."""
        try:
            # Получаем информацию о файле
            file_info = self._make_request("getFile", {"file_id": file_id})
            file_path = file_info["result"]["file_path"]
            
            # Скачиваем файл
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                f.write(response.content)
                
            logger.debug(f"Фото сохранено: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Не удалось скачать фото: {e}")
            return None
