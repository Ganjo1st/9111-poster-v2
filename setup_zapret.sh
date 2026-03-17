#!/bin/bash
set -e

echo "📥 Скачиваем готовые бинарники zapret..."
cd /tmp
rm -rf zapret

# Скачиваем готовую сборку для Linux
wget https://github.com/bol-van/zapret/releases/download/v70/zapret-v70.tar.gz
tar -xzf zapret-v70.tar.gz
cd zapret-v70

echo "⚙️ Копируем бинарники в /usr/local/bin..."
sudo cp tpws/tpws /usr/local/bin/
sudo cp nfq/nfqws /usr/local/bin/ 2>/dev/null || true
sudo cp ip2net/ip2net /usr/local/bin/ 2>/dev/null || true

# Даем права на выполнение
sudo chmod +x /usr/local/bin/tpws

echo "✅ zapret готов"
ls -la /usr/local/bin/tpws
