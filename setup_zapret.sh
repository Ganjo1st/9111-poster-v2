#!/bin/bash
set -e

echo "📥 Скачиваем готовые бинарники zapret..."
cd /tmp
rm -rf zapret*

# Скачиваем готовую сборку для Linux
wget https://github.com/bol-van/zapret/releases/download/v70/zapret-v70.tar.gz
tar -xzf zapret-v70.tar.gz

# Переходим в папку
cd zapret-v70

echo "📁 Содержимое архива:"
ls -la

echo "📁 Ищем бинарники в папке binaries:"
ls -la binaries/

echo "📁 Для x86_64:"
ls -la binaries/x86_64/ || echo "Папка x86_64 не найдена"

echo "📁 Для x86:"
ls -la binaries/x86/ || echo "Папка x86 не найдена"

# Копируем правильный бинарник для Linux x86_64
if [ -f "binaries/x86_64/tpws" ]; then
    echo "✅ Найден бинарник для x86_64"
    sudo cp binaries/x86_64/tpws /usr/local/bin/
elif [ -f "binaries/x86/tpws" ]; then
    echo "✅ Найден бинарник для x86"
    sudo cp binaries/x86/tpws /usr/local/bin/
else
    echo "❌ Бинарник tpws не найден!"
    echo "🔍 Ищем все tpws файлы:"
    find . -name "tpws" -type f | grep -v "init.d" | grep -v "config"
    exit 1
fi

# Даем права на выполнение
sudo chmod +x /usr/local/bin/tpws

echo "✅ tpws скопирован:"
file /usr/local/bin/tpws
ls -la /usr/local/bin/tpws
