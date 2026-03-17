#!/bin/bash
set -e

echo "📥 Скачиваем NoDPI (рабочая версия)..."
cd /tmp
rm -rf NoDPI
git clone https://github.com/ValdikSS/GoodbyeDPI.git NoDPI
cd NoDPI

echo "🔧 Компилируем GoodbyeDPI..."
make

echo "✅ NoDPI готов к запуску"
echo "📁 Содержимое папки:"
ls -la
