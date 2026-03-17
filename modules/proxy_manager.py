#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для управления прокси.
Использует только проверенный список из репозитория Proctor.
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
    
    # ЕДИНСТВЕННЫЙ ИСТОЧНИК - проверенные российские прокси
    PROXY_SOURCE = "https://raw.githubusercontent.com/Ganjo1st/Proctor/main/proxies_russia.txt"
    
    def __init__(self):
        self.working_proxies = []
        self.current_proxy = None
        self.all_proxies = []
        self._load_proxies()
    
    def _load_proxies(self) -> List[str]:
        """
        Загружает прокси из единственного источника.
        
        Returns:
            Список прокси
        """
        try:
            logger.info(f"📡 Загрузка прокси из: {self.PROXY_SOURCE}")
            response = requests.get(self.PROXY_SOURCE, timeout=10)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                self.all_proxies = []
                
                for line in lines:
                    proxy = line.strip()
                    # Проверяем формат ip:port
                    if proxy and ':' in proxy and len(proxy.split(':')) == 2:
                        self.all_proxies.append(proxy)
                
                logger.info(f"✅ Загружено {len(self.all_proxies)} прокси")
                return self.all_proxies
            else:
                logger.error(f"❌ Ошибка загрузки: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Не удалось загрузить прокси: {e}")
            return []
    
    def test_proxy_advanced(self, proxy: str) -> Tuple[bool, float, Dict]:
        """
        Продвинутое тестирование прокси с проверкой HTTPS и скорости.
        
        Args:
            proxy: Прокси в формате ip:port
            
        Returns:
            (работает_ли, скорость_в_секундах, детали)
        """
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        results = {}
        
        # Тест 1: HTTP подключение
        try:
            start = time.time()
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            http_time = time.time() - start
            
            if response.status_code == 200:
                results['http'] = {
                    'success': True,
                    'time': http_time,
                    'ip': response.json().get('origin', 'unknown')
                }
                logger.debug(f"  ✅ HTTP: {http_time:.2f}с, IP: {results['http']['ip']}")
            else:
                results['http'] = {'success': False, 'code': response.status_code}
        except Exception as e:
            results['http'] = {'success': False, 'error': str(e)}
        
        # Тест 2: HTTPS подключение (критично для 9111.ru)
        try:
            start = time.time()
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                verify=True
            )
            https_time = time.time() - start
            
            if response.status_code == 200:
                results['https'] = {
                    'success': True,
                    'time': https_time,
                    'ip': response.json().get('origin', 'unknown')
                }
                logger.debug(f"  ✅ HTTPS: {https_time:.2f}с, IP: {results['https']['ip']}")
            else:
                results['https'] = {'success': False, 'code': response.status_code}
        except requests.exceptions.ProxyError as e:
            if 'Tunnel connection failed' in str(e):
                results['https'] = {'success': False, 'error': 'Tunnel failed - proxy does not support HTTPS'}
            else:
                results['https'] = {'success': False, 'error': str(e)}
        except Exception as e:
            results['https'] = {'success': False, 'error': str(e)}
        
        # Тест 3: Проверка на target URL (9111.ru)
        try:
            start = time.time()
            response = requests.get(
                'https://9111.ru',
                proxies=proxies,
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                allow_redirects=True
            )
            target_time = time.time() - start
            
            if response.status_code in [200, 302, 403]:
                results['target'] = {
                    'success': True,
                    'time': target_time,
                    'code': response.status_code
                }
                logger.debug(f"  ✅ Target (9111.ru): {target_time:.2f}с, код: {response.status_code}")
            else:
                results['target'] = {'success': False, 'code': response.status_code}
        except Exception as e:
            results['target'] = {'success': False, 'error': str(e)}
        
        # Определяем общий успех - нужно, чтобы работал HTTPS
        overall_success = (
            results.get('http', {}).get('success', False) and 
            results.get('https', {}).get('success', False)
        )
        
        # Берем среднюю скорость
        avg_speed = float('inf')
        if overall_success:
            speeds = []
            if 'http' in results and results['http'].get('success'):
                speeds.append(results['http']['time'])
            if 'https' in results and results['https'].get('success'):
                speeds.append(results['https']['time'])
            if speeds:
                avg_speed = sum(speeds) / len(speeds)
        
        return overall_success, avg_speed, results
    
    def find_working_proxy(self, max_attempts: int = None) -> Optional[str]:
        """
        Находит рабочий прокси из загруженного списка.
        
        Args:
            max_attempts: Максимальное количество попыток (если None - все прокси)
            
        Returns:
            Рабочий прокси или None
        """
        logger.info("🔍 Поиск рабочего прокси из загруженного списка...")
        
        if not self.all_proxies:
            logger.error("❌ Список прокси пуст")
            return None
        
        # Перемешиваем для случайного выбора
        proxies_to_test = self.all_proxies.copy()
        random.shuffle(proxies_to_test)
        
        if max_attempts:
            proxies_to_test = proxies_to_test[:max_attempts]
        
        logger.info(f"📋 Будет проверено прокси: {len(proxies_to_test)}")
        
        working_proxies = []
        tested = 0
        
        for proxy in proxies_to_test:
            tested += 1
            logger.info(f"🔄 Тест {tested}/{len(proxies_to_test)}: {proxy}")
            
            works, speed, details = self.test_proxy_advanced(proxy)
            
            if works:
                working_proxies.append((proxy, speed, details))
                logger.info(f"  ✅ РАБОТАЕТ! Скорость: {speed:.2f}с")
                logger.info(f"     HTTP: {details.get('http', {}).get('time', 0):.2f}с, "
                           f"HTTPS: {details.get('https', {}).get('time', 0):.2f}с")
                
                # Если нашли быстрый прокси с HTTPS, возвращаем сразу
                if speed < 3.0:
                    self.current_proxy = proxy
                    logger.info(f"🎯 Выбран быстрый прокси: {proxy} ({speed:.2f}с)")
                    return proxy
            else:
                # Логируем причину отказа
                if 'https' in details and not details['https'].get('success'):
                    if 'Tunnel failed' in str(details['https'].get('error', '')):
                        logger.info(f"  ❌ HTTPS не поддерживается (туннелирование)")
                    else:
                        logger.info(f"  ❌ HTTPS ошибка: {details['https'].get('error', 'unknown')}")
                elif 'http' in details and not details['http'].get('success'):
                    logger.info(f"  ❌ HTTP ошибка")
        
        if working_proxies:
            # Сортируем по скорости и выбираем лучший
            working_proxies.sort(key=lambda x: x[1])
            best_proxy = working_proxies[0][0]
            best_speed = working_proxies[0][1]
            
            self.current_proxy = best_proxy
            logger.info(f"🎯 Выбран лучший прокси: {best_proxy} ({best_speed:.2f}с)")
            return best_proxy
        
        logger.error("❌ НЕ НАЙДЕНО РАБОЧИХ ПРОКСИ!")
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
