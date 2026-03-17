#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной скрипт для GitHub Actions.
ФИНАЛЬНАЯ СТРАТЕГИЯ: прокси с первого запроса!
"""

import os
import sys
import logging
import time
import random
import json
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Импорты модулей проекта
from modules.github_actions_auth import Auth9111
from modules.telegram_bot_parser import TelegramRSSParser
from modules.publication_api import PublicationAPI
from modules.rubric_mapper import get_rubric_id
from modules.cookie_manager import CookieManager
from modules.proxy_manager import ProxyManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/poster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('9111_poster')

def main():
    """Основная функция."""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК 9111 POSTER (ФИНАЛЬНАЯ ВЕРСИЯ)")
    logger.info("📋 Стратегия: прокси -> куки -> авторизация -> публикация")
    logger.info("="
