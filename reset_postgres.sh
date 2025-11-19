#!/bin/bash
# Скрипт для полного сброса PostgreSQL на сервере
# Использовать только когда база повреждена!

set -e

echo "🔄 Остановка контейнеров..."
docker-compose down

echo "🗑️ Поиск и удаление volume PostgreSQL..."
# Находим правильное имя volume (может быть с префиксом директории)
VOLUME_NAME=$(docker volume ls -q | grep postgres-data || true)

if [ -n "$VOLUME_NAME" ]; then
    echo "Найден volume: $VOLUME_NAME"
    docker volume rm $VOLUME_NAME
    echo "✅ Volume удалён"
else
    echo "⚠️  Volume не найден (возможно уже удалён)"
fi

echo ""
echo "🚀 Запуск контейнеров с чистой базой..."
docker-compose up -d

echo ""
echo "⏳ Ожидание запуска PostgreSQL (30 секунд)..."
sleep 30

echo ""
echo "✅ Проверка статуса контейнеров..."
docker-compose ps

echo ""
echo "📊 Проверка таблиц в PostgreSQL..."
docker-compose exec -T postgres psql -U neuromagic_user -d neuromagic -c "\dt" || echo "⚠️  Не удалось подключиться к БД"

echo ""
echo "🔍 Логи приложения (последние 30 строк)..."
docker-compose logs app --tail 30

echo ""
echo "🌐 Проверка HTTP..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000 || echo "⚠️  Сайт не отвечает"

echo ""
echo "✅ Готово! Проверьте работу сайта."
