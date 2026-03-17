#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для управления прокси.
Улучшенная версия с проверкой HTTPS и поддержки туннелирования.
"""

import logging
import random
import time
import requests
from typing import List, Tuple, Optional, Dict
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class ProxyManager:
    """Класс для управления прокси."""
    
    # Расширенный список российских прокси из разных источников
    RUSSIAN_PROXIES = [
        # HTTP/HTTPS прокси (проверенные)
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
        '193.124.176.139:8443',
        '193.124.176.139:8888',
        '193.124.176.142:8080',
        '193.124.176.142:8443',
        '193.124.176.177:8080',
        '193.124.176.177:8443',
        '193.124.176.187:8080',
        '193.124.176.187:8443',
        '193.124.176.188:8080',
        '193.124.176.188:8443',
        '193.124.176.202:8080',
        '193.124.176.202:8443',
        '193.124.176.209:8080',
        '193.124.176.209:8443',
        '193.124.176.215:8080',
        '193.124.176.215:8443',
        '193.124.176.218:8080',
        '193.124.176.218:8443',
        '193.124.176.221:8080',
        '193.124.176.221:8443',
        '193.124.176.224:8080',
        '193.124.176.224:8443',
        '193.124.176.227:8080',
        '193.124.176.227:8443',
        '193.124.176.230:8080',
        '193.124.176.230:8443',
    ]
    
    # Источники свежих прокси
    PROXY_SOURCES = [
        'https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_ru.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
        'https://raw.githubusercontent.com/ya-panel/proxy-list/main/proxy_list_http.txt',
        'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list-data.txt',
        'https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_http.txt',
        'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    ]
    
    def __init__(self):
        self.working_proxies = []
        self.current_proxy = None
    
    def fetch_fresh_proxies(self, max_per_source: int = 100) -> List[str]:
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
                        # Фильтруем только валидные прокси с правильным форматом
                        if proxy and ':' in proxy and len(proxy.split(':')) == 2:
                            # Проверяем, что это не приватный IP
                            ip_parts = proxy.split(':')[0].split('.')
                            if len(ip_parts) == 4:
                                first_octet = int(ip_parts[0])
                                # Исключаем приватные диапазоны
                                if not (first_octet == 10 or 
                                       (first_octet == 172 and 16 <= int(ip_parts[1]) <= 31) or
                                       (first_octet == 192 and ip_parts[1] == '168')):
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
                # 403 тоже считаем успехом - значит прокси работает, но сайт блокирует
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
    
    def find_working_proxy(self, max_attempts: int = 100, target_url: str = "https://9111.ru") -> Optional[str]:
        """
        Находит рабочий прокси с приоритетом на HTTPS поддержку.
        
        Args:
            max_attempts: Максимальное количество попыток
            target_url: Целевой URL для тестирования
            
        Returns:
            Рабочий прокси или None
        """
        logger.info("🔍 Поиск рабочего российского прокси (с проверкой HTTPS)...")
        
        # Собираем все прокси
        all_proxies = []
        
        # 1. Сначала наши проверенные
        all_proxies.extend(self.RUSSIAN_PROXIES)
        
        # 2. Пробуем загрузить свежие
        try:
            fresh_proxies = self.fetch_fresh_proxies(max_per_source=100)
            all_proxies.extend(fresh_proxies)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки свежих прокси: {e}")
        
        # Убираем дубликаты и перемешиваем
        all_proxies = list(set(all_proxies))
        random.shuffle(all_proxies)
        
        logger.info(f"📋 Всего прокси для проверки: {len(all_proxies)}")
        
        working_proxies = []
        tested = 0
        
        for proxy in all_proxies[:max_attempts]:
            tested += 1
            logger.info(f"🔄 Тест {tested}/{min(max_attempts, len(all_proxies))}: {proxy}")
            
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
        
        logger.error("❌ НЕ НАЙДЕНО РАБОЧИХ ПРОКСИ С HTTPS ПОДДЕРЖКОЙ!")
        return None
    
    def parallel_proxy_check(self, proxies: List[str], max_workers: int = 10) -> List[Tuple[str, float]]:
        """
        Параллельная проверка нескольких прокси.
        
        Args:
            proxies: Список прокси для проверки
            max_workers: Максимальное количество потоков
            
        Returns:
            Список рабочих прокси с их скоростью
        """
        working = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.test_proxy_advanced, proxy): proxy 
                for proxy in proxies
            }
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    works, speed, details = future.result()
                    if works:
                        working.append((proxy, speed))
                        logger.info(f"✅ {proxy} - {speed:.2f}с")
                except Exception as e:
                    logger.debug(f"❌ {proxy} - ошибка: {e}")
        
        return sorted(working, key=lambda x: x[1])
    
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
