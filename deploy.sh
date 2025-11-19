#!/bin/bash

# Скрипт для первоначального деплоя на сервер

set -e

echo "🚀 Начинаем деплой Нейромагии..."

# Создаём директорию проекта
echo "📁 Создаём директорию /opt/neuromagic..."
mkdir -p /opt/neuromagic
cd /opt/neuromagic

# Клонируем репозиторий (если ещё не склонирован)
if [ ! -d ".git" ]; then
    echo "📦 Клонируем репозиторий..."
    git clone https://github.com/Starlight19973/magic_ai.git .
else
    echo "🔄 Обновляем репозиторий..."
    git pull origin main
fi

# Создаём .env файл
echo "🔑 Создаём .env файл..."
cat > .env << 'EOF'
SECRET_KEY=prod_secret_key_2024_neuromagic_ultra_secure
TELEGRAM_BOT_TOKEN=8528801413:AAFW7dH8I-soM2m_6cUC_HZGIf_DnDEtbYQ
TELEGRAM_CHAT_ID=-5020049520
EOF

# Создаём необходимые директории
echo "📂 Создаём директории для данных..."
mkdir -p data logs nginx/ssl

# Устанавливаем Docker (если не установлен)
if ! command -v docker &> /dev/null; then
    echo "🐳 Устанавливаем Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Устанавливаем Docker Compose (если не установлен)
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Устанавливаем Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Собираем образы
echo "🔨 Собираем Docker образы..."
docker-compose build --no-cache

# Инициализируем базу данных
echo "💾 Инициализируем базу данных..."
docker-compose run --rm app python -c "
from app.database import init_db
import asyncio
asyncio.run(init_db())
print('✅ База данных инициализирована')
"

# Создаём тестового пользователя
echo "👤 Создаём тестового пользователя..."
docker-compose run --rm app python create_test_user.py || true

# Запускаем приложение с nginx
echo "▶️  Запускаем приложение..."
docker-compose --profile production up -d

# Проверяем статус
echo "✅ Проверяем статус контейнеров..."
docker-compose ps

# Показываем логи
echo "📋 Логи приложения:"
docker-compose logs --tail=50

echo ""
echo "✨ Деплой завершён!"
echo "🌐 Приложение доступно по адресу: http://138.124.15.60"
echo ""
echo "Полезные команды:"
echo "  docker-compose logs -f              # Просмотр логов"
echo "  docker-compose restart              # Перезапуск"
echo "  docker-compose down                 # Остановка"
echo "  docker-compose up -d                # Запуск без nginx"
echo "  docker-compose --profile production up -d  # Запуск с nginx"

