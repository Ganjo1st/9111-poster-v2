#!/bin/bash
set -e

echo "📥 Скачиваем готовые бинарники zapret..."
cd /tmp
rm -rf zapret*

wget https://github.com/bol-van/zapret/releases/download/v70/zapret-v70.tar.gz
tar -xzf zapret-v70.tar.gz
cd zapret-v70

# Копируем правильный бинарник для Linux x86_64
if [ -f "binaries/x86_64/tpws" ]; then
    echo "✅ Найден бинарник для x86_64"
    sudo cp binaries/x86_64/tpws /usr/local/bin/
else
    echo "❌ Бинарник tpws не найден!"
    exit 1
fi

sudo chmod +x /usr/local/bin/tpws
echo "✅ tpws скопирован:"
ls -la /usr/local/bin/tpws
