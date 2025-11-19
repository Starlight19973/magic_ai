# ⚡ Быстрый старт деплоя

## 🎯 Цель
Развернуть Нейромагию на сервере **138.124.15.60**

## 📋 Данные для входа
```
IP: 138.124.15.60
User: root
Password: PFIwOaXLAo08Wz
```

---

## 🚀 ВАРИАНТ 1: Автоматический деплой (GitHub Actions)

### Шаг 1: Настройте GitHub Secrets

Перейдите: https://github.com/Starlight19973/magic_ai/settings/secrets/actions

Добавьте 3 секрета:

| Name | Value |
|------|-------|
| `SERVER_HOST` | `138.124.15.60` |
| `SERVER_USER` | `root` |
| `SERVER_PASSWORD` | `PFIwOaXLAo08Wz` |

### Шаг 2: Первый запуск на сервере

Подключитесь к серверу и выполните:

```bash
ssh root@138.124.15.60

# Установка Docker и Git
curl -fsSL https://get.docker.com | sh
apt install git -y
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Клонирование проекта
mkdir -p /opt/neuromagic && cd /opt/neuromagic
git clone https://github.com/Starlight19973/magic_ai.git .

# Создание .env
cat > .env << 'EOF'
SECRET_KEY=prod_secret_key_2024_neuromagic_ultra_secure
TELEGRAM_BOT_TOKEN=8528801413:AAFW7dH8I-soM2m_6cUC_HZGIf_DnDEtbYQ
TELEGRAM_CHAT_ID=-5020049520
EOF

# Создание директорий
mkdir -p data logs nginx/ssl

# Сборка и запуск
docker-compose build
docker-compose run --rm app python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
docker-compose run --rm app python create_test_user.py
docker-compose --profile production up -d
```

### Шаг 3: Проверка

Откройте в браузере: **http://138.124.15.60**

### Шаг 4: Автообновления

Теперь при каждом `git push` в `main` сайт будет обновляться автоматически! 🎉

---

## 🛠️ ВАРИАНТ 2: Ручной деплой

Используйте готовый скрипт `deploy.sh`:

```bash
ssh root@138.124.15.60
curl -o deploy.sh https://raw.githubusercontent.com/Starlight19973/magic_ai/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

---

## ✅ Проверка работы

После деплоя проверьте:

1. **Сайт работает**: http://138.124.15.60
2. **Логин**: Username: `testuser`, Password: `test123`
3. **Контейнеры запущены**:
   ```bash
   docker-compose ps
   ```
4. **Логи без ошибок**:
   ```bash
   docker-compose logs -f
   ```

---

## 🔧 Полезные команды

### На сервере

```bash
cd /opt/neuromagic

# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление с GitHub
git pull origin main
docker-compose build
docker-compose --profile production up -d

# Проверка статуса
docker-compose ps
docker stats
```

### Локально

```bash
# Push изменений (запустит автодеплой)
git add .
git commit -m "Update"
git push origin main

# Проверка GitHub Actions
# https://github.com/Starlight19973/magic_ai/actions
```

---

## 🌐 После покупки домена

1. **Настройте DNS A-запись**:
   ```
   @ → 138.124.15.60
   www → 138.124.15.60
   ```

2. **Получите SSL сертификат**:
   ```bash
   apt install certbot -y
   certbot certonly --standalone -d ваш-домен.ru -d www.ваш-домен.ru
   cp /etc/letsencrypt/live/ваш-домен.ru/*.pem /opt/neuromagic/nginx/ssl/
   ```

3. **Обновите nginx.conf**:
   - Раскомментируйте блок HTTPS
   - Измените `server_name` на ваш домен
   - Перезапустите: `docker-compose restart nginx`

---

## 🐛 Проблемы?

### Контейнеры не запускаются
```bash
docker-compose logs
docker-compose down && docker-compose --profile production up -d
```

### Порт занят
```bash
netstat -tulpn | grep :80
# Если что-то запущено - остановите
```

### База данных не создаётся
```bash
rm -f data/neuromagic.db
docker-compose run --rm app python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

---

## 📚 Подробная документация

- **Полная инструкция**: `SERVER_SETUP.md`
- **Деплой на production**: `DEPLOY.md`
- **GitHub Actions**: `.github/workflows/deploy.yml`

---

**🎉 Готово! Ваш сайт на http://138.124.15.60**

