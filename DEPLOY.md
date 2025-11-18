# 🚀 Деплой Нейромагии на сервер

## 📋 Содержание

1. [Требования](#требования)
2. [Быстрый старт](#быстрый-старт)
3. [Настройка переменных окружения](#настройка-переменных-окружения)
4. [Деплой с Docker](#деплой-с-docker)
5. [Деплой с Nginx](#деплой-с-nginx)
6. [SSL сертификаты](#ssl-сертификаты)
7. [Обслуживание](#обслуживание)
8. [Мониторинг](#мониторинг)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Требования

### На сервере должно быть установлено:

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Git**
- Минимум **1 GB RAM**
- Минимум **10 GB** свободного места

### Проверка установки:

```bash
docker --version
docker-compose --version
git --version
```

---

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Starlight19973/magic_ai.git
cd magic_ai
```

### 2. Создайте .env файл

```bash
cp .env.production .env
nano .env  # или vim/vi
```

**Обязательно измените**:
- `SECRET_KEY` — длинный случайный ключ
- `TELEGRAM_BOT_TOKEN` — токен вашего бота
- `TELEGRAM_CHAT_ID` — ID чата для заявок

### 3. Запустите через Docker

```bash
make docker-build
make docker-up
```

Или без Make:

```bash
docker-compose build
docker-compose up -d
```

### 4. Проверьте работу

```bash
curl http://localhost:8000
```

Откройте в браузере: `http://ваш-сервер:8000`

---

## ⚙️ Настройка переменных окружения

### Файл `.env` на сервере:

```env
# ОБЯЗАТЕЛЬНО изменить!
SECRET_KEY=ваш-очень-длинный-случайный-ключ-минимум-32-символа
TELEGRAM_BOT_TOKEN=6123456789:AAHdqTxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789

# Можно оставить по умолчанию
APP_ENV=production
DATABASE_URL=sqlite+aiosqlite:///data/neuromagic.db
CONTACT_EMAIL=hello@neuro-magic.ru
SITE_NAME=Нейромагия
```

### Генерация SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🐳 Деплой с Docker

### Основные команды:

```bash
# Сборка образа
make docker-build

# Запуск контейнеров
make docker-up

# Остановка
make docker-down

# Логи
make docker-logs

# Перезапуск
make docker-restart

# Вход в контейнер
make docker-shell
```

### Структура Docker:

```
docker-compose.yml
├── app          # Основное приложение (порт 8000)
└── nginx        # Reverse proxy (порты 80, 443)
```

### Volumes (персистентность):

- `./data:/app/data` — база данных SQLite
- `./logs:/app/logs` — логи приложения

---

## 🌐 Деплой с Nginx (Production)

### 1. Настройте домен

Убедитесь, что ваш домен указывает на сервер:

```bash
# A запись
neuro-magic.ru → IP_СЕРВЕРА
www.neuro-magic.ru → IP_СЕРВЕРА
```

### 2. Обновите nginx.conf

Отредактируйте `nginx/nginx.conf`:

```nginx
server_name neuro-magic.ru www.neuro-magic.ru;
```

Укажите ваш домен вместо `neuro-magic.ru`.

### 3. Запустите с Nginx

```bash
make deploy-nginx
```

Или:

```bash
docker-compose --profile production up -d
```

### 4. Проверьте

```bash
curl http://ваш-домен
```

---

## 🔒 SSL сертификаты (Let's Encrypt)

### Вариант 1: Certbot в контейнере

```bash
# Установите certbot
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d neuro-magic.ru \
  -d www.neuro-magic.ru \
  --email hello@neuro-magic.ru \
  --agree-tos

# Скопируйте сертификаты
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/neuro-magic.ru/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/neuro-magic.ru/privkey.pem nginx/ssl/

# Перезапустите Nginx
make docker-restart
```

### Вариант 2: Автоматическое обновление

Добавьте в crontab:

```bash
# Обновление сертификатов каждые 2 месяца
0 0 1 */2 * docker run --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew && docker-compose restart nginx
```

---

## 🛠️ Обслуживание

### Обновление приложения

```bash
# Подтяните изменения из Git
git pull origin main

# Пересоберите и перезапустите
make deploy
```

### Бэкап базы данных

```bash
# Автоматический бэкап
make backup

# Или вручную
docker-compose exec app cp /app/data/neuromagic.db /app/backups/backup_$(date +%Y%m%d).db
```

### Восстановление из бэкапа

```bash
docker-compose down
cp backups/backup_20250115.db data/neuromagic.db
docker-compose up -d
```

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Только приложения
docker-compose logs -f app

# Только Nginx
docker-compose logs -f nginx

# Последние 100 строк
docker-compose logs --tail=100 app
```

### Очистка

```bash
# Удалить неиспользуемые Docker образы
docker system prune -a

# Полная очистка (ВНИМАНИЕ: удалит volumes!)
make clean
```

---

## 📊 Мониторинг

### Healthcheck

Docker автоматически проверяет здоровье контейнера каждые 30 секунд.

Проверка вручную:

```bash
docker inspect neuromagic-app | grep -A 10 Health
```

### Системные ресурсы

```bash
# Использование ресурсов контейнерами
docker stats

# Место на диске
df -h
du -sh data/
```

### Логирование

Логи автоматически ротируются Docker.

Настройка в `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 🐛 Troubleshooting

### Приложение не запускается

```bash
# Проверьте логи
docker-compose logs app

# Проверьте .env файл
cat .env

# Пересоберите образ
docker-compose build --no-cache
```

### База данных не создаётся

```bash
# Проверьте права на директорию
ls -la data/

# Создайте директорию вручную
mkdir -p data
chmod 755 data

# Перезапустите
docker-compose restart
```

### Порт 8000 занят

```bash
# Найдите процесс
lsof -i :8000
# или
netstat -tulpn | grep 8000

# Измените порт в docker-compose.yml
ports:
  - "8001:8000"  # Внешний 8001, внутренний 8000
```

### Nginx не работает

```bash
# Проверьте конфигурацию
docker-compose exec nginx nginx -t

# Проверьте логи
docker-compose logs nginx

# Перезагрузите конфигурацию
docker-compose exec nginx nginx -s reload
```

### SSL сертификаты не работают

```bash
# Проверьте файлы
ls -la nginx/ssl/

# Проверьте права
chmod 644 nginx/ssl/*.pem

# Проверьте срок действия
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates
```

### Telegram бот не отправляет заявки

```bash
# Проверьте переменные окружения
docker-compose exec app env | grep TELEGRAM

# Проверьте логи
docker-compose logs app | grep Telegram

# Тестовая отправка
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=Test message"
```

---

## 🔄 CI/CD (опционально)

### GitHub Actions

Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/magic_ai
            git pull origin main
            make deploy
```

---

## 📈 Масштабирование

### Увеличение воркеров

В `Dockerfile`:

```dockerfile
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "8"]
```

### PostgreSQL вместо SQLite

В `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: neuromagic
      POSTGRES_USER: neuromagic
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data

  app:
    environment:
      - DATABASE_URL=postgresql+asyncpg://neuromagic:secure_password@postgres:5432/neuromagic
```

---

## ✅ Чеклист деплоя

- [ ] Сервер с Docker установлен
- [ ] Репозиторий склонирован
- [ ] `.env` файл настроен (SECRET_KEY, Telegram)
- [ ] Docker образ собран (`make docker-build`)
- [ ] Контейнеры запущены (`make docker-up`)
- [ ] Приложение доступно на порту 8000
- [ ] База данных создана
- [ ] Telegram бот работает (тест заявки)
- [ ] Nginx настроен (если используется)
- [ ] SSL сертификаты установлены (для HTTPS)
- [ ] Бэкапы настроены
- [ ] Мониторинг настроен

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте раздел [Troubleshooting](#troubleshooting)
2. Посмотрите логи: `make docker-logs`
3. Проверьте документацию Docker
4. Создайте Issue на GitHub

---

## 🎉 Готово!

Ваше приложение Нейромагия развёрнуто и готово к работе!

**URL**: `http://ваш-домен:8000` (без Nginx) или `https://ваш-домен` (с Nginx)

