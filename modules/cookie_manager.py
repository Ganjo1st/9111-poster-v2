#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для управления куками.
Поддерживает форматы Netscape и JSON.
"""

import re
import logging
import json
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CookieManager:
    """Класс для загрузки и конвертации кук."""
    
    @staticmethod
    def parse_netscape_cookie_line(line: str) -> Optional[Dict[str, str]]:
        """
        Парсит одну строку куки в формате Netscape.
        
        Args:
            line: Строка из cookies.txt
            
        Returns:
            Словарь с данными куки или None
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        parts = line.split('\t')
        if len(parts) >= 7:
            return {
                'domain': parts[0],
                'flag': parts[1],
                'path': parts[2],
                'secure': parts[3],
                'expiry': parts[4],
                'name': parts[5],
                'value': parts[6]
            }
        return None
    
    @staticmethod
    def load_netscape_cookies(filepath: str) -> Dict[str, str]:
        """
        Загружает куки из файла в формате Netscape.
        
        Args:
            filepath: Путь к файлу с куками
            
        Returns:
            Словарь с куками {имя: значение}
        """
        cookies_dict = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    cookie_data = CookieManager.parse_netscape_cookie_line(line)
                    if cookie_data:
                        cookies_dict[cookie_data['name']] = cookie_data['value']
                        logger.debug(f"Загружена кука: {cookie_data['name']}")
            
            logger.info(f"✅ Загружено {len(cookies_dict)} кук из {filepath}")
            return cookies_dict
            
        except FileNotFoundError:
            logger.error(f"❌ Файл не найден: {filepath}")
            return {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кук: {e}")
            return {}
    
    @staticmethod
    def cookies_to_json(cookies_dict: Dict[str, str]) -> str:
        """
        Конвертирует словарь кук в JSON строку для секретов GitHub.
        
        Args:
            cookies_dict: Словарь с куками
            
        Returns:
            JSON строка
        """
        return json.dumps(cookies_dict, ensure_ascii=False, indent=2)
    
    @staticmethod
    def cookies_from_json(json_str: str) -> Dict[str, str]:
        """
        Загружает куки из JSON строки.
        
        Args:
            json_str: JSON строка с куками
            
        Returns:
            Словарь с куками
        """
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return {}
    
    @staticmethod
    def apply_cookies_to_session(session, cookies_dict: Dict[str, str]):
        """
        Применяет куки к сессии requests.
        
        Args:
            session: Сессия requests
            cookies_dict: Словарь с куками
        """
        for name, value in cookies_dict.items():
            session.cookies.set(name, value, domain='.9111.ru', path='/')
        logger.info(f"🍪 Применено {len(cookies_dict)} кук к сессии")
    
    @staticmethod
    def create_cookies_from_parts(
        user_hash: str,
        uuk: str,
        myq: str = "eaf0f0faf1fd626e775643ef02c89d95",
        au: str = None
    ) -> Dict[str, str]:
        """
        Создает словарь кук из отдельных компонентов.
        
        Args:
            user_hash: Хеш пользователя
            uuk: UUK токен
            myq: MYQ токен
            au: AU токен
            
        Returns:
            Словарь с куками
        """
        cookies = {
            'user_hash': user_hash,
            'uuk': uuk,
            'myq': myq,
        }
        
        if au:
            cookies['au'] = au
        
        # Фильтруем пустые значения
        cookies = {k: v for k, v in cookies.items() if v}
        
        logger.info(f"✅ Создано {len(cookies)} кук из компонентов")
        return cookies
