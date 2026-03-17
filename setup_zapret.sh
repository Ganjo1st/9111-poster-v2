#!/bin/bash
set -e

echo "📥 Скачиваем zapret..."
git clone https://github.com/bol-van/zapret /tmp/zapret
cd /tmp/zapret

echo "🔧 Компилируем zapret..."
make -j4

echo "⚙️ Копируем бинарники в /usr/local/bin..."
sudo cp /tmp/zapret/tpws /usr/local/bin/
sudo cp /tmp/zapret/nfqws /usr/local/bin/
sudo cp /tmp/zapret/ip2net /usr/local/bin/

echo "✅ zapret готов к использованию"
