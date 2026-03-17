#!/bin/bash
set -e

echo "📥 Скачиваем готовые бинарники zapret..."
cd /tmp
rm -rf zapret*

# Скачиваем готовую сборку для Linux
wget https://github.com/bol-van/zapret/releases/download/v70/zapret-v70.tar.gz
tar -xzf zapret-v70.tar.gz

# Находим папку с бинарниками
cd zapret-v70

echo "📁 Содержимое архива:"
ls -la

# Ищем tpws - он может быть в разных местах
if [ -f "tpws" ]; then
    echo "✅ Найден tpws в корне"
    sudo cp tpws /usr/local/bin/
elif [ -f "bin/tpws" ]; then
    echo "✅ Найден tpws в bin/"
    sudo cp bin/tpws /usr/local/bin/
elif [ -f "tpws/tpws" ]; then
    echo "✅ Найден tpws в tpws/"
    sudo cp tpws/tpws /usr/local/bin/
else
    echo "🔍 Ищем tpws рекурсивно..."
    find . -name "tpws" -type f
    TPWS_PATH=$(find . -name "tpws" -type f | head -1)
    if [ -n "$TPWS_PATH" ]; then
        echo "✅ Найден tpws по пути: $TPWS_PATH"
        sudo cp "$TPWS_PATH" /usr/local/bin/
    else
        echo "❌ tpws не найден!"
        exit 1
    fi
fi

# Даем права на выполнение
sudo chmod +x /usr/local/bin/tpws

echo "✅ zapret готов"
ls -la /usr/local/bin/tpws
