#!/bin/bash
set -e

echo "📥 Скачиваем zapret..."
cd /tmp
rm -rf zapret
git clone https://github.com/bol-van/zapret.git
cd zapret

echo "🔧 Компилируем zapret..."
./configure.sh
make

echo "⚙️ Копируем бинарники..."
sudo cp tpws/tpws /usr/local/bin/
sudo cp nfq/nfqws /usr/local/bin/ 2>/dev/null || true
sudo cp ip2net/ip2net /usr/local/bin/ 2>/dev/null || true

echo "✅ zapret готов"
ls -la /usr/local/bin/tpws
