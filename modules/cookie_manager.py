#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для управления куками в формате Netscape.
Конвертирует куки из формата Netscape в формат для requests.
"""

import re
import logging
import json
from http.cookiejar import MozillaCookieJar
from typing import Dict, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)
