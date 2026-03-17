#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Добавляем корневую директорию в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import re
import logging
from typing import Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from src.browser_manager import BrowserManager
from src.telegram_parser import TelegramParser
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ... (весь остальной код класса Post9111 остается без изменений)
