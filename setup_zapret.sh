#!/bin/bash
set -e

echo "📥 Скачиваем zapret..."
rm -rf /tmp/zapret
git clone https://github.com/bol-van/zapret /tmp/zapret
cd /tmp/zapret

echo "🔧 Конфигурируем и компилируем zapret..."
./configure.sh
make -j4

echo "⚙️ Копируем бинарники в /usr/local/bin..."
sudo cp /tmp/zapret/tpws/tpws /usr/local/bin/
sudo cp /tmp/zapret/nfq/nfqws /usr/local/bin/ || true
sudo cp /tmp/zapret/ip2net/ip2net /usr/local/bin/ || true

echo "✅ zapret готов к использованию"
