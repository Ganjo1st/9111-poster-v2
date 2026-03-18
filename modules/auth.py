#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль авторизации на 9111.ru.
Рабочая версия из проекта 9111-poster-v2-main.
"""

import logging
import time
import pickle
import json
import re
from typing import Optional, Dict, Tuple

import requests
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class Auth9111:
    """Класс для авторизации на 9111.ru."""
    
    BASE_URL = "https://9111.ru"
    LOGIN_URL = f"{BASE_URL}/login/"
    PROFILE_URL = f"{BASE_URL}/my/"
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self._setup_session()
    
    def _setup_session(self):
        """Настраивает сессию с заголовками как в рабочем проекте."""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
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
        Выполняет вход на сайт 9111.ru.
        
        Args:
            email: Email пользователя
            password: Пароль
            
        Returns:
            True если вход успешен
        """
        logger.info("🔑 Попытка входа на 9111.ru...")
        
        try:
            # 1. Загружаем страницу входа
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
                        return True
                    else:
                        logger.warning("⚠️ Страница профиля загружена, но признаки авторизации не найдены")
                else:
                    logger.error(f"❌ Ошибка при проверке профиля: {profile_response.status_code}")
            else:
                logger.error(f"❌ Ошибка при отправке формы входа: {login_response.status_code}")
                
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
                        
            return False
            
        except Exception as e:
            logger.debug(f"Ошибка при проверке авторизации: {e}")
            return False
    
    def get_session(self) -> requests.Session:
        """Возвращает текущую сессию."""
        return self.session
