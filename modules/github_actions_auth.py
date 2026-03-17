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
            proxies: Прокси для обхода блокировок (например, {'http': 'http://46.17.47.48:80', 'https': 'http://46.17.47.48:80'})
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
            'User-Agent': self.ua.random if hasattr(self, 'ua') else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            
            # Проверяем, что сессия все еще работает
            try:
                test_response = self.session.get(self.PROFILE_URL, timeout=10)
                if test_response.status_code == 200:
                    logger.info("✅ Сессия с новым прокси работает")
                    return True
                else:
                    logger.warning("⚠️ Сессия с новым прокси не работает")
                    return False
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке сессии: {e}")
                return False
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
        
        # Ищем в meta тегах
        match = re.search(r'<meta[^>]+name="csrf-token"[^>]+content="([^"]+)"', html)
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
            
            # Небольшая задержка как у человека
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
                    # Ищем признаки авторизации
                    page_text = profile_response.text.lower()
                    
                    if 'личный кабинет' in page_text or email.lower() in page_text or 'выйти' in page_text:
                        logger.info("✅ Вход выполнен успешно")
                        
                        # Сохраняем куки для отладки
                        cookies_dict = self.session.cookies.get_dict()
                        logger.info(f"🍪 Получено куки: {list(cookies_dict.keys())}")
                        
                        return True
                    else:
                        logger.warning("⚠️ Страница профиля загружена, но признаки авторизации не найдены")
                        # Сохраняем часть страницы для отладки
                        debug_text = profile_response.text[:500]
                        logger.debug(f"Начало страницы: {debug_text}")
                else:
                    logger.error(f"❌ Ошибка при проверке профиля: {profile_response.status_code}")
            else:
                logger.error(f"❌ Ошибка при отправке формы входа: {login_response.status_code}")
                
        except requests.exceptions.ProxyError as e:
            logger.error(f"❌ Ошибка прокси: {e}")
            if self.proxies:
                logger.info("🔄 Пробуем без прокси...")
                self.proxies = None
                self.session = self._create_session()
                return self.login(email, password)
                
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут при подключении")
        except Exception as e:
            logger.exception(f"❌ Неожиданная ошибка: {e}")
        
        return False
    
    def save_cookies(self, filepath: str = "cookies.pkl"):
        """Сохраняет куки в файл."""
        with open(filepath, 'wb') as f:
            pickle.dump(self.session.cookies, f)
        logger.info(f"💾 Cookies сохранены в {filepath}")
    
    def load_cookies(self, filepath: str = "cookies.pkl") -> bool:
        """Загружает куки из файла."""
        try:
            with open(filepath, 'rb') as f:
                self.session.cookies.update(pickle.load(f))
            logger.info(f"📂 Cookies загружены из {filepath}")
            return True
        except FileNotFoundError:
            logger.warning(f"⚠️ Файл cookies не найден: {filepath}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки cookies: {e}")
            return False
    
    def get_cookies_json(self) -> str:
        """Возвращает куки в формате JSON для сохранения в секреты."""
        cookies_dict = self.session.cookies.get_dict()
        return json.dumps(cookies_dict, ensure_ascii=False, indent=2)
    
    def load_cookies_from_json(self, cookies_json: str) -> bool:
        """Загружает куки из JSON строки."""
        try:
            cookies_dict = json.loads(cookies_json)
            self.session.cookies.update(cookies_dict)
            logger.info(f"📂 Загружено {len(cookies_dict)} cookies из JSON")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки cookies из JSON: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Проверяет, авторизована ли сессия."""
        try:
            response = self.session.get(self.PROFILE_URL, timeout=10)
            if response.status_code == 200:
                # Ищем признаки авторизации
                page_text = response.text.lower()
                if 'личный кабинет' in page_text or 'выйти' in page_text:
                    return True
            return False
        except Exception as e:
            logger.debug(f"Ошибка при проверке авторизации: {e}")
            return False
