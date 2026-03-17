#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для парсинга Telegram канала через RSS.
Использует feedparser для получения постов.
"""

import logging
import feedparser
import re
from typing import List, Dict, Optional
from datetime import datetime
import html

logger = logging.getLogger(__name__)

class TelegramRSSParser:
    """Парсер Telegram канала через RSS."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TelegramRSSParser")
    
    def get_posts(self, channel_id: str, token: str = None, limit: int = 5) -> List[Dict]:
        """
        Получает посты из Telegram канала через RSS.
        
        Args:
            channel_id: ID канала (например, @channel или https://t.me/channel)
            token: Не используется, оставлен для совместимости
            limit: Максимальное количество постов
            
        Returns:
            Список словарей с постами
        """
        self.logger.info(f"📱 Получение постов из канала: {channel_id}")
        
        # Формируем RSS URL
        if channel_id.startswith('@'):
            channel_name = channel_id[1:]
        elif 't.me/' in channel_id:
            channel_name = channel_id.split('t.me/')[-1].split('/')[0]
        else:
            channel_name = channel_id
        
        rss_url = f"https://t.me/s/{channel_name}"
        self.logger.info(f"📡 RSS URL: {rss_url}")
        
        try:
            # Парсим RSS
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                self.logger.warning("❌ Нет записей в RSS")
                return []
            
            self.logger.info(f"✅ Найдено {len(feed.entries)} записей")
            
            posts = []
            for entry in feed.entries[:limit]:
                post = self._parse_entry(entry)
                if post:
                    posts.append(post)
            
            self.logger.info(f"📄 Получено {len(posts)} постов")
            return posts
            
        except Exception as e:
            self.logger.exception(f"❌ Ошибка парсинга RSS: {e}")
            return []
    
    def _parse_entry(self, entry) -> Optional[Dict]:
        """
        Парсит одну запись RSS.
        
        Args:
            entry: Запись из feedparser
            
        Returns:
            Словарь с данными поста или None
        """
        try:
            # Извлекаем заголовок
            title = entry.get('title', '')
            if title:
                title = html.unescape(title)
            
            # Извлекаем содержимое
            content = ''
            if hasattr(entry, 'content'):
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            
            if content:
                content = html.unescape(content)
                # Удаляем HTML теги
                content = re.sub(r'<[^>]+>', '', content)
            
            # Извлекаем ссылку
            link = entry.get('link', '')
            
            # Извлекаем дату
            published = entry.get('published', '')
            
            # Извлекаем изображение
            image_url = None
            if hasattr(entry, 'links'):
                for link in entry.links:
                    if link.get('type', '').startswith('image/'):
                        image_url = link.get('href')
                        break
            
            # Если не нашли в links, ищем в content
            if not image_url and content:
                img_match = re.search(r'<img[^>]+src="([^"]+)"', content)
                if img_match:
                    image_url = img_match.group(1)
            
            post = {
                'title': title,
                'content': content,
                'link': link,
                'published': published,
                'image_url': image_url
            }
            
            self.logger.debug(f"Пост: {title[:50]}...")
            return post
            
        except Exception as e:
            self.logger.exception(f"Ошибка парсинга записи: {e}")
            return None
    
    def extract_text_from_html(self, html_text: str) -> str:
        """Извлекает чистый текст из HTML."""
        if not html_text:
            return ''
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', html_text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# Для обратной совместимости
TelegramRSSParser = TelegramRSSParser
