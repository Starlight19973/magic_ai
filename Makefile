.PHONY: help install dev lint test docker-build docker-up docker-down docker-logs docker-restart

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "🔧 Разработка:"
	@echo "  make install          - Установить зависимости"
	@echo "  make dev              - Запустить в режиме разработки"
	@echo "  make lint             - Проверить код"
	@echo "  make test             - Запустить тесты"
	@echo ""
	@echo "🐳 Docker (Production):"
	@echo "  make docker-build     - Собрать Docker образ"
	@echo "  make docker-up        - Запустить контейнеры"
	@echo "  make docker-down      - Остановить контейнеры"
	@echo "  make docker-logs      - Показать логи"
	@echo "  make docker-restart   - Перезапустить контейнеры"
	@echo "  make docker-shell     - Зайти в контейнер"
	@echo ""
	@echo "📦 Деплой:"
	@echo "  make deploy           - Полный деплой (build + up)"
	@echo "  make backup           - Бэкап базы данных"

# ============================================
# Разработка (локально)
# ============================================
install:
	python -m pip install -r requirements.txt

dev:
	quart --app main:app --debug run

lint:
	ruff check app

test:
	pytest

# ============================================
# Docker команды
# ============================================
docker-build:
	@echo "🔨 Сборка Docker образа..."
	docker-compose build

docker-up:
	@echo "🚀 Запуск контейнеров..."
	docker-compose up -d
	@echo "✅ Приложение запущено на http://localhost:8000"

docker-down:
	@echo "🛑 Остановка контейнеров..."
	docker-compose down

docker-logs:
	@echo "📋 Логи контейнеров..."
	docker-compose logs -f

docker-restart:
	@echo "🔄 Перезапуск контейнеров..."
	docker-compose restart

docker-shell:
	@echo "🐚 Вход в контейнер..."
	docker-compose exec app /bin/bash

# ============================================
# Production деплой
# ============================================
deploy:
	@echo "🚀 Деплой приложения..."
	docker-compose build
	docker-compose up -d
	@echo "✅ Деплой завершён!"

deploy-nginx:
	@echo "🚀 Деплой с Nginx..."
	docker-compose --profile production up -d
	@echo "✅ Деплой с Nginx завершён!"

# ============================================
# Утилиты
# ============================================
backup:
	@echo "💾 Создание бэкапа БД..."
	mkdir -p backups
	docker-compose exec app cp /app/data/neuromagic.db /app/backups/neuromagic_backup.db
	@echo "✅ Бэкап создан!"

clean:
	@echo "🧹 Очистка..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v
	@echo "✅ Очистка завершена!"

