#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🔍 Проверка прокси перед запуском"
echo "=========================================="

# Проверяем, задан ли прокси
if [ -z "$PROXY" ]; then
    echo -e "${RED}❌ PROXY не задан!${NC}"
    exit 1
fi

echo -e "${YELLOW}📡 Тестируем прокси: $PROXY${NC}"
echo "------------------------------------------"

# Тест 1: Базовая доступность прокси
echo "Тест 1: Проверка доступности прокси..."
if curl -x "http://$PROXY" -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://example.com | grep -q "200"; then
    echo -e "${GREEN}✅ Прокси доступен${NC}"
else
    echo -e "${RED}❌ Прокси не отвечает${NC}"
    exit 1
fi

# Тест 2: Проверка работы с HTTP
echo "Тест 2: Проверка HTTP соединения..."
HTTP_TEST=$(curl -x "http://$PROXY" -s -o /dev/null -w "%{http_code}" --max-time 10 http://httpbin.org/get)
if [ "$HTTP_TEST" = "200" ]; then
    echo -e "${GREEN}✅ HTTP работает (код: $HTTP_TEST)${NC}"
else
    echo -e "${RED}❌ HTTP не работает (код: $HTTP_TEST)${NC}"
    exit 1
fi

# Тест 3: Проверка работы с HTTPS
echo "Тест 3: Проверка HTTPS соединения..."
HTTPS_TEST=$(curl -x "http://$PROXY" -s -o /dev/null -w "%{http_code}" --max-time 10 https://httpbin.org/get)
if [ "$HTTPS_TEST" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS работает (код: $HTTPS_TEST)${NC}"
else
    echo -e "${RED}❌ HTTPS не работает (код: $HTTPS_TEST)${NC}"
    echo -e "${YELLOW}⚠️  Это может быть проблемой для Selenium!${NC}"
    exit 1
fi

# Тест 4: Проверка скорости
echo "Тест 4: Проверка скорости соединения..."
SPEED_TEST=$(curl -x "http://$PROXY" -s -o /dev/null -w "%{time_total}" --max-time 10 https://httpbin.org/get)
if (( $(echo "$SPEED_TEST < 2" | bc -l) )); then
    echo -e "${GREEN}✅ Скорость хорошая: ${SPEED_TEST}с${NC}"
elif (( $(echo "$SPEED_TEST < 5" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Скорость средняя: ${SPEED_TEST}с${NC}"
else
    echo -e "${RED}❌ Скорость низкая: ${SPEED_TEST}с${NC}"
    exit 1
fi

# Тест 5: Проверка доступа к Google (нужно для Chrome)
echo "Тест 5: Проверка доступа к Google..."
GOOGLE_TEST=$(curl -x "http://$PROXY" -s -o /dev/null -w "%{http_code}" --max-time 10 https://www.google.com)
if [ "$GOOGLE_TEST" = "200" ]; then
    echo -e "${GREEN}✅ Google доступен${NC}"
else
    echo -e "${RED}❌ Google недоступен (код: $GOOGLE_TEST)${NC}"
    exit 1
fi

# Тест 6: Проверка доступа к GitHub (нужно для ChromeDriver)
echo "Тест 6: Проверка доступа к GitHub..."
GITHUB_TEST=$(curl -x "http://$PROXY" -s -o /dev/null -w "%{http_code}" --max-time 10 https://github.com)
if [ "$GITHUB_TEST" = "200" ]; then
    echo -e "${GREEN}✅ GitHub доступен${NC}"
else
    echo -e "${RED}❌ GitHub недоступен (код: $GITHUB_TEST)${NC}"
    exit 1
fi

# Тест 7: Проверка доступа к Chrome for Testing API
echo "Тест 7: Проверка доступа к Chrome for Testing API..."
CHROME_API_TEST=$(curl -x "http://$PROXY" -s -o /dev/null -w "%{http_code}" --max-time 10 https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json)
if [ "$CHROME_API_TEST" = "200" ]; then
    echo -e "${GREEN}✅ Chrome API доступен${NC}"
else
    echo -e "${RED}❌ Chrome API недоступен (код: $CHROME_API_TEST)${NC}"
    echo -e "${YELLOW}⚠️  Это критично для Selenium!${NC}"
    exit 1
fi

echo "------------------------------------------"
echo -e "${GREEN}✅✅✅ Все тесты пройдены! Прокси работает корректно.${NC}"
echo "=========================================="

# Сохраняем результат проверки
echo "PROXY_WORKING=true" >> $GITHUB_ENV
