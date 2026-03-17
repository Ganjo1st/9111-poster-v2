#!/bin/bash
set -e

echo "📥 Скачиваем готовые бинарники zapret..."
cd /tmp
rm -rf zapret*

wget https://github.com/bol-van/zapret/releases/download/v70/zapret-v70.tar.gz
tar -xzf zapret-v70.tar.gz
cd zapret-v70

# Копируем бинарники для Linux x86_64
if [ -f "binaries/x86_64/tpws" ] && [ -f "binaries/x86_64/nfqws" ]; then
    echo "✅ Найдены бинарники для x86_64"
    sudo cp binaries/x86_64/tpws /usr/local/bin/
    sudo cp binaries/x86_64/nfqws /usr/local/bin/
else
    echo "❌ Бинарники не найдены!"
    exit 1
fi

sudo chmod +x /usr/local/bin/tpws /usr/local/bin/nfqws
echo "✅ Бинарники скопированы:"
ls -la /usr/local/bin/tpws /usr/local/bin/nfqws
