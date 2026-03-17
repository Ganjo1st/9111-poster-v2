#!/bin/bash
set -e

echo "📥 Скачиваем zapret..."
rm -rf /tmp/zapret
git clone https://github.com/bol-van/zapret /tmp/zapret
cd /tmp/zapret

echo "🔧 Компилируем zapret..."
make -j4

echo "⚙️ Копируем бинарники в /usr/local/bin..."
# Копируем tpws (он нам нужен)
sudo cp /tmp/zapret/tpws/tpws /usr/local/bin/ || true
# Опционально копируем остальное
sudo cp /tmp/zapret/nfq/nfqws /usr/local/bin/ 2>/dev/null || true
sudo cp /tmp/zapret/ip2net/ip2net /usr/local/bin/ 2>/dev/null || true

# Даем права на выполнение
sudo chmod +x /usr/local/bin/tpws 2>/dev/null || true

echo "✅ zapret готов к использованию"
echo "🔍 Проверяем наличие tpws:"
ls -la /usr/local/bin/tpws || echo "❌ tpws не найден!"
