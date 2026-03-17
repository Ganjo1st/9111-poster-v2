#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для управления прокси.
Поиск, тестирование и выбор рабочих российских прокси.
"""

import logging
import random
import time
import requests
from typing import List, Tuple, Optional, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ProxyManager:
    """Класс для управления прокси."""
    
    # Расширенный список российских прокси
    RUSSIAN_PROXIES = [
        '46.17.47.48:80',
        '46.29.162.166:80',
        '85.198.96.242:3128',
        '46.47.197.210:3128',
        '94.181.80.170:80',
        '94.181.146.80:80',
        '95.167.22.44:3128',
        '95.167.22.45:3128',
        '95.167.22.46:3128',
        '95.167.22.47:3128',
        '95.167.22.48:3128',
        '95.167.22.49:3128',
        '95.167.22.50:3128',
        '95.167.22.51:3128',
        '95.167.22.52:3128',
        '95.167.22.53:3128',
        '95.167.22.54:3128',
        '95.167.22.55:3128',
        '95.167.22.56:3128',
        '95.167.22.57:3128',
        '95.167.22.58:3128',
        '95.167.22.59:3128',
        '95.167.22.60:3128',
        '95.167.22.61:3128',
        '95.167.22.62:3128',
        '95.167.22.63:3128',
        '95.167.22.64:3128',
        '95.167.22.65:3128',
        '95.167.22.66:3128',
        '95.167.22.67:3128',
        '95.167.22.68:3128',
        '95.167.22.69:3128',
        '95.167.22.70:3128',
        '185.118.67.66:8080',
        '185.118.67.109:8080',
        '185.118.67.159:8080',
        '185.118.67.211:8080',
        '185.118.67.220:8080',
        '185.118.67.243:8080',
        '91.220.163.202:8080',
        '91.220.163.203:8080',
        '91.220.163.204:8080',
        '91.220.163.205:8080',
        '91.220.163.206:8080',
        '91.220.163.207:8080',
        '91.220.163.208:8080',
        '91.220.163.209:8080',
        '91.220.163.210:8080',
        '94.181.44.217:8080',
        '94.181.44.218:8080',
        '94.181.44.219:8080',
        '94.181.44.220:8080',
        '94.181.44.221:8080',
        '94.181.44.222:8080',
        '94.181.44.223:8080',
        '94.181.44.224:8080',
        '94.181.44.225:8080',
        '94.181.44.226:8080',
        '94.181.44.227:8080',
        '94.181.44.228:8080',
        '94.181.44.229:8080',
        '94.181.44.230:8080',
    ]
    
    # Источники свежих прокси
    PROXY_SOURCES = [
        'https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_ru.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
        'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
        'https://raw.githubusercontent.com/ya-panel/proxy-list/main/proxy_list_http.txt',
        'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list-data.txt',
    ]
    
    def __init__(self):
        self.working_proxies = []
        self.current_proxy = None
    
    def fetch_fresh_proxies(self, max_per_source: int = 50) -> List[str]:
        """
        Получает свежие прокси из внешних источников.
        
        Args:
            max_per_source: Максимальное количество прокси из каждого источника
            
        Returns:
            Список прокси
        """
        fresh_proxies = []
        
        for source in self.PROXY_SOURCES:
            try:
                logger.info(f"📡 Загрузка прокси из: {source}")
                response = requests.get(source, timeout=10)
                
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    count = 0
                    
                    for line in lines[:max_per_source]:
                        proxy = line.strip()
                        # Фильтруем только валидные прокси
                        if proxy and ':' in proxy and len(proxy.split(':')) == 2:
                            fresh_proxies.append(proxy)
                            count += 1
                    
                    logger.info(f"✅ Загружено {count} прокси из {source}")
                else:
                    logger.warning(f"⚠️ Ошибка загрузки из {source}: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить из {source}: {e}")
        
        # Убираем дубликаты
        fresh_proxies = list(set(fresh_proxies))
        logger.info(f"📊 Всего свежих прокси: {len(fresh_proxies)}")
        
        return fresh_proxies
    
    def test_proxy(self, proxy: str, test_url: str = "https://9111.ru", timeout: int = 10) -> Tuple[bool, float]:
        """
        Тестирует работоспособность прокси.
        
        Args:
            proxy: Прокси в формате ip:port
            test_url: URL для тестирования
            timeout: Таймаут в секундах
            
        Returns:
            (работает_ли, скорость_в_секундах)
        """
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        test_urls = [
            test_url,
            "http://httpbin.org/ip",
            "https://api.ipify.org",
            "http://example.com"
        ]
        
        for url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(
                    url,
                    proxies=proxies,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    logger.debug(f"  ✅ {url} - {elapsed:.2f}с")
                    
                    # Для тестового URL проверяем IP
                    if url == "http://httpbin.org/ip" and elapsed < timeout:
                        return True, elapsed
                else:
                    logger.debug(f"  ❌ {url} - {response.status_code}")
                    
            except requests.exceptions.ConnectTimeout:
                logger.debug(f"  ⏰ Таймаут: {url}")
            except requests.exceptions.ProxyError as e:
                logger.debug(f"  🔌 Ошибка прокси: {e}")
            except Exception as e:
                logger.debug(f"  ❌ Ошибка: {e}")
        
        return False, float('inf')
    
    def find_working_proxy(self, max_attempts: int = 50, target_url: str = "https://9111.ru") -> Optional[str]:
        """
        Находит рабочий прокси для целевого сайта.
        
        Args:
            max_attempts: Максимальное количество попыток
            target_url: Целевой URL для тестирования
            
        Returns:
            Рабочий прокси или None
        """
        logger.info("🔍 Поиск рабочего российского прокси...")
        
        # Сначала пробуем свежие прокси из внешних источников
        try:
            fresh_proxies = self.fetch_fresh_proxies()
            all_proxies = list(set(fresh_proxies + self.RUSSIAN_PROXIES))
        except:
            all_proxies = self.RUSSIAN_PROXIES.copy()
        
        # Перемешиваем для случайного выбора
        random.shuffle(all_proxies)
        
        logger.info(f"📋 Всего прокси для проверки: {len(all_proxies)}")
        
        tested = 0
        working_proxies = []
        
        for proxy in all_proxies[:max_attempts * 2]:
            tested += 1
            logger.info(f"🔄 Тест {tested}/{min(max_attempts * 2, len(all_proxies))}: {proxy}")
            
            works, speed = self.test_proxy(proxy, test_url=target_url)
            
            if works:
                working_proxies.append((proxy, speed))
                logger.info(f"  ✅ РАБОТАЕТ! Скорость: {speed:.2f}с")
                
                # Если нашли достаточно быстрый прокси, возвращаем
                if speed < 5.0:
                    self.current_proxy = proxy
                    logger.info(f"🎯 Выбран быстрый прокси: {proxy} ({speed:.2f}с)")
                    return proxy
            
            if tested >= max_attempts and working_proxies:
                break
        
        if working_proxies:
            # Сортируем по скорости и выбираем самый быстрый
            working_proxies.sort(key=lambda x: x[1])
            best_proxy = working_proxies[0][0]
            best_speed = working_proxies[0][1]
            
            self.current_proxy = best_proxy
            logger.info(f"🎯 Выбран лучший прокси: {best_proxy} ({best_speed:.2f}с)")
            return best_proxy
        
        logger.warning("❌ Рабочих прокси не найдено")
        return None
    
    def get_proxy_dict(self, proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Возвращает словарь прокси для requests.
        
        Args:
            proxy: Прокси в формате ip:port или None для текущего
            
        Returns:
            Словарь с прокси или None
        """
        if proxy is None:
            proxy = self.current_proxy
        
        if not proxy:
            return None
        
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    def update_session_proxy(self, session, proxy: Optional[str] = None):
        """
        Обновляет прокси в сессии.
        
        Args:
            session: Сессия requests
            proxy: Прокси в формате ip:port или None для текущего
        """
        proxy_dict = self.get_proxy_dict(proxy)
        
        if proxy_dict:
            session.proxies.update(proxy_dict)
            logger.info(f"🔌 Прокси обновлен в сессии: {proxy or self.current_proxy}")
            return True
        
        logger.warning("⚠️ Нет прокси для обновления")
        return False
