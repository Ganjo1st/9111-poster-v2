#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для управления куками в формате Netscape.
Конвертирует куки из формата Netscape в формат для requests.
"""

import re
import logging
from http.cookiejar import MozillaCookieJar
from typing import Dict, List
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class CookieManager:
    """Класс для загрузки и конвертации кук из формата Netscape."""
    
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
                content = f.read()
            
            # Парсим каждую строку
            for line in content.split('\n'):
                line = line.strip()
                
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue
                
                # Формат Netscape: domain flag path secure expiry name value
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain = parts[0]
                    flag = parts[1]
                    path = parts[2]
                    secure = parts[3]
                    expiry = parts[4]
                    name = parts[5]
                    value = parts[6]
                    
                    cookies_dict[name] = value
                    logger.debug(f"Загружена кука: {name}={value[:20]}...")
            
            logger.info(f"✅ Загружено {len(cookies_dict)} кук из {filepath}")
            return cookies_dict
            
        except FileNotFoundError:
            logger.error(f"❌ Файл не найден: {filepath}")
            return {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кук: {e}")
            return {}
    
    @staticmethod
    def save_cookies_to_env(cookies_dict: Dict[str, str], env_var_name: str = "COOKIES_JSON") -> str:
        """
        Сохраняет куки в формате JSON для использования в секретах GitHub.
        
        Args:
            cookies_dict: Словарь с куками
            env_var_name: Имя переменной окружения
            
        Returns:
            JSON строка с куками
        """
        import json
        return json.dumps(cookies_dict, ensure_ascii=False)
    
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
    def get_cookies_from_files(directory: str = ".") -> Dict[str, str]:
        """
        Ищет файлы с куками в директории и загружает их.
        
        Args:
            directory: Директория для поиска
            
        Returns:
            Объединенный словарь кук
        """
        all_cookies = {}
        cookie_files = list(Path(directory).glob("cookies_*.txt"))
        
        if not cookie_files:
            logger.warning("⚠️ Файлы с куками не найдены")
            return {}
        
        logger.info(f"🔍 Найдено файлов с куками: {len(cookie_files)}")
        
        for cookie_file in cookie_files:
            logger.info(f"📄 Загрузка: {cookie_file}")
            cookies = CookieManager.load_netscape_cookies(str(cookie_file))
            all_cookies.update(cookies)
        
        logger.info(f"✅ Всего загружено кук: {len(all_cookies)}")
        return all_cookies
    
    @staticmethod
    def create_cookies_from_parts(
        user_hash: str,
        uuk: str,
        geo: str = "91-817-1",
        myq: str = "eaf0f0faf1fd626e775643ef02c89d95",
        au: str = "%7B%22u%22%3A2368040%2C%22k%22%3A%22aa8ca3729252da5450cdb0862352503d%22%2C%22t%22%3A1773759120%7D"
    ) -> Dict[str, str]:
        """
        Создает словарь кук из отдельных компонентов.
        
        Args:
            user_hash: Хеш пользователя
            uuk: UUK токен
            geo: Гео-токен
            myq: MYQ токен
            au: AU токен
            
        Returns:
            Словарь с куками
        """
        return {
            'user_hash': user_hash,
            'uuk': uuk,
            'geo': geo,
            'myq': myq,
            'au': au,
            'log_question_source': '3',
            'tmp_view_article': 'yes'
        }
