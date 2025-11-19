#!/bin/bash
# Скрипт для полного сброса PostgreSQL на сервере
# Использовать только когда база повреждена!

set -e

echo "🔄 Остановка контейнеров..."
docker-compose down

echo "🗑️ Удаление volume PostgreSQL..."
docker volume rm neuromagic_postgres-data 2>/dev/null || true

echo "🚀 Запуск контейнеров с чистой базой..."
docker-compose up -d

echo "⏳ Ожидание запуска PostgreSQL (30 секунд)..."
sleep 30

echo "✅ Проверка статуса контейнеров..."
docker-compose ps

echo ""
echo "📊 Проверка таблиц в PostgreSQL..."
docker-compose exec -T postgres psql -U neuromagic_user -d neuromagic -c "\dt"

echo ""
echo "🔍 Проверка логов приложения..."
docker-compose logs app --tail 20

echo ""
echo "✅ Готово! Проверьте работу сайта."
