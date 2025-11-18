# Используем официальный Python образ
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Neuromagic <hello@neuro-magic.ru>"
LABEL description="Neuromagic AI Learning Platform"

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём директорию для базы данных
RUN mkdir -p /app/data

# Создаём непривилегированного пользователя
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV QUART_APP=main:app

# Открываем порт
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000').read()"

# Запускаем приложение через Hypercorn (production ASGI server)
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]

