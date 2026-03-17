#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль авторизации для GitHub Actions.
Использует requests для входа на 9111.ru с обходом блокировок.
"""

import os
import logging
import time
import pickle
import json
import re
from typing import Optional, Dict, Any

import requests
from fake_useragent import UserAgent
import cloudscraper

logger = logging.getLogger(__name__)

class Auth9111:
    """Класс для авторизации на 9111.ru через requests с обходом блокировок."""
    
    BASE_URL = "https://9111.ru"
    LOGIN_URL = f"{BASE_URL}/login/"
    PROFILE_URL = f"{BASE_URL}/my/"
    
    def __init__(self, proxies: dict = None):
        """
        Инициализация авторизации.
        
        Args:
            proxies: Прокси для обхода блокировок
        """
        self.proxies = proxies
        self.session = self._create_session()
        self.ua = UserAgent()
        
    def _create_session(self) -> requests.Session:
        """Создает сессию с обходом CloudFlare."""
        scraper = cloudscraper.create_scraper(
            interpreter='js',
            delay=15,
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Настраиваем заголовки как у реального браузера
        scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        if self.proxies:
            scraper.proxies.update(self.proxies)
            logger.info(f"🔌 Прокси настроены: {self.proxies}")
        
        return scraper
    
    def update_proxy(self, proxies: dict) -> bool:
        """
        Обновляет прокси в существующей сессии.
        
        Args:
            proxies: Новый словарь прокси
            
        Returns:
            True если обновление успешно
        """
        if proxies:
            self.proxies = proxies
            self.session.proxies.update(proxies)
            logger.info(f"🔌 Прокси обновлены: {proxies}")
            return True
        return False
    
    def _get_csrf_token(self, html: str) -> Optional[str]:
        """Извлекает CSRF токен из HTML."""
        # Ищем в скрытых полях формы
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', html)
        if match:
            return match.group(1)
        
        # Ищем в JavaScript переменных
        match = re.search(r'csrf_token["\']?\s*:\s*["\']([^"\']+)', html)
        if match:
            return match.group(1)
        
        return None
    
    def login(self, email: str, password: str) -> bool:
        """
        Выполняет вход на сайт.
        
        Args:
            email: Email пользователя
            password: Пароль
            
        Returns:
            True если вход успешен
        """
        logger.info("🔑 Попытка входа на 9111.ru...")
        
        try:
            # 1. Загружаем страницу входа для получения CSRF токена
            logger.info("📡 Загрузка страницы входа...")
            response = self.session.get(self.LOGIN_URL, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ Не удалось загрузить страницу входа: {response.status_code}")
                return False
            
            # 2. Извлекаем CSRF токен
            csrf_token = self._get_csrf_token(response.text)
            
            if csrf_token:
                logger.info(f"✅ CSRF токен найден")
            else:
                logger.warning("⚠️ CSRF токен не найден, пробуем без него")
            
            time.sleep(2)
            
            # 3. Подготавливаем данные для входа
            login_data = {
                'login': email,
                'password': password,
                'remember': 'on',
                'submit': 'Войти',
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # 4. Отправляем POST запрос
            logger.info("📤 Отправка формы входа...")
            login_response = self.session.post(
                self.LOGIN_URL,
                data=login_data,
                allow_redirects=True,
                timeout=30,
                headers={
                    'Referer': self.LOGIN_URL,
                    'Origin': self.BASE_URL,
                }
            )
            
            # 5. Проверяем успешность входа
            if login_response.status_code in [200, 302]:
                logger.info(f"✅ Форма отправлена, код: {login_response.status_code}")
                
                # Проверяем через профиль
                logger.info("🔍 Проверка профиля...")
                profile_response = self.session.get(self.PROFILE_URL, timeout=30)
                
                if profile_response.status_code == 200:
                    page_text = profile_response.text.lower()
                    
                    if 'личный кабинет' in page_text or 'выйти' in page_text:
                        logger.info("✅ Вход выполнен успешно")
                        cookies_dict = self.session.cookies.get_dict()
                        logger.info(f"🍪 Получено куки: {list(cookies_dict.keys())}")
                        return True
                    else:
                        logger.warning("⚠️ Страница профиля загружена, но признаки авторизации не найдены")
                else:
                    logger.error(f"❌ Ошибка при проверке профиля: {profile_response.status_code}")
            else:
                logger.error(f"❌ Ошибка при отправке формы входа: {login_response.status_code}")
                
        except requests.exceptions.ProxyError as e:
            logger.error(f"❌ Ошибка прокси: {e}")
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут при подключении")
        except Exception as e:
            logger.exception(f"❌ Неожиданная ошибка: {e}")
        
        return False
    
    def get_cookies_json(self) -> str:
        """Возвращает куки в формате JSON."""
        cookies_dict = self.session.cookies.get_dict()
        return json.dumps(cookies_dict, ensure_ascii=False, indent=2)
    
    def is_authenticated(self) -> bool:
        """Проверяет, авторизована ли сессия."""
        try:
            response = self.session.get(self.PROFILE_URL, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                page_text = response.text.lower()
                
                auth_indicators = [
                    'личный кабинет',
                    'выйти',
                    'профиль',
                    'мои публикации',
                ]
                
                for indicator in auth_indicators:
                    if indicator in page_text:
                        logger.debug(f"Найден признак авторизации: {indicator}")
                        return True
                
                if self.session.cookies.get('user_hash') and self.session.cookies.get('uuk'):
                    logger.debug("Есть куки user_hash и uuk, считаем авторизованными")
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug(f"Ошибка при проверке авторизации: {e}")
            return False
