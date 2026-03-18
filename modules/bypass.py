#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для обхода блокировок РКН.
Использует методы из рабочего проекта (setup_zapret.sh, blacklist.txt).
"""

import logging
import subprocess
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class BypassManager:
    """Класс для управления обходом блокировок."""
    
    def __init__(self):
        self.blacklist_file = Path("blacklist.txt")
        self.setup_script = Path("setup_zapret.sh")
        
    def setup_zapret(self) -> bool:
        """
        Запускает скрипт setup_zapret.sh для настройки обхода блокировок.
        Должен запускаться с правами root.
        
        Returns:
            True если успешно, иначе False
        """
        if not self.setup_script.exists():
            logger.error(f"❌ Файл {self.setup_script} не найден")
            return False
            
        logger.info("🔧 Настройка обхода блокировок (zapret)...")
        try:
            # Запускаем скрипт с bash
            result = subprocess.run(
                ['bash', str(self.setup_script)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ Zapret настроен успешно")
                logger.debug(f"Вывод: {result.stdout}")
                return True
            else:
                logger.error(f"❌ Ошибка настройки zapret: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Таймаут при настройке zapret")
            return False
        except Exception as e:
            logger.exception(f"❌ Исключение: {e}")
            return False
    
    def load_blacklist(self) -> list:
        """
        Загружает черный список доменов/IP из blacklist.txt.
        
        Returns:
            Список заблокированных ресурсов
        """
        if not self.blacklist_file.exists():
            logger.warning(f"⚠️ Файл {self.blacklist_file} не найден")
            return []
            
        blacklist = []
        try:
            with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        blacklist.append(line)
            
            logger.info(f"📋 Загружено {len(blacklist)} записей из blacklist.txt")
            return blacklist
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки blacklist: {e}")
            return []
    
    def is_blocked(self, domain: str) -> bool:
        """
        Проверяет, находится ли домен в черном списке.
        
        Args:
            domain: Домен для проверки
            
        Returns:
            True если домен заблокирован
        """
        blacklist = self.load_blacklist()
        return domain in blacklist
    
    def get_bypass_headers(self) -> dict:
        """
        Возвращает заголовки для обхода блокировок.
        
        Returns:
            Словарь с заголовками
        """
        return {
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
        }
