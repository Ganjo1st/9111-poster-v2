#!/bin/bash
set -e

echo "📥 Скачиваем NoDPI..."
cd /tmp
rm -rf NoDPI
git clone https://github.com/aeronik16/NoDPI_july2025.git NoDPI
cd NoDPI

echo "✅ NoDPI готов к запуску"
