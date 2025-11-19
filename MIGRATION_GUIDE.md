# Руководство по миграции с SQLite на PostgreSQL

## 📋 Обзор

Этот проект теперь поддерживает как SQLite (для разработки), так и PostgreSQL (для production).

## 🔄 Миграция существующих данных

### Шаг 1: Запустить PostgreSQL локально (Docker)

```bash
# Установите пароль в .env
echo "POSTGRES_PASSWORD=your_secure_password" >> .env

# Запустите только PostgreSQL
docker-compose up -d postgres

# Проверьте что PostgreSQL запущен
docker-compose ps
docker-compose logs postgres
```

### Шаг 2: Настроить переменные окружения

Добавьте в `.env`:

```env
# PostgreSQL настройки
POSTGRES_DB=neuromagic
POSTGRES_USER=neuromagic_user
POSTGRES_PASSWORD=your_secure_password

# DATABASE_URL для миграции
DATABASE_URL=postgresql+asyncpg://neuromagic_user:your_secure_password@localhost:5432/neuromagic
```

### Шаг 3: Установить зависимости

```bash
pip install -r requirements.txt
```

### Шаг 4: Запустить миграцию

```bash
python migrate_to_postgres.py
```

Скрипт:
- ✅ Создаст таблицы в PostgreSQL
- ✅ Скопирует всех пользователей
- ✅ Скопирует прогресс по курсам
- ✅ Скопирует email верификации

### Шаг 5: Проверить данные

```bash
# Подключитесь к PostgreSQL
docker-compose exec postgres psql -U neuromagic_user -d neuromagic

# Проверьте таблицы
\dt

# Проверьте пользователей
SELECT id, username, email FROM users;

# Выход
\q
```

## 🚀 Деплой на Production

### Для Docker (рекомендуется)

1. **Обновите `.env` на сервере:**

```env
POSTGRES_DB=neuromagic
POSTGRES_USER=neuromagic_user
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
```

2. **Запустите с Docker Compose:**

```bash
docker-compose down
docker-compose up -d
```

Docker автоматически:
- Запустит PostgreSQL контейнер
- Создаст volume для данных
- Подключит приложение к PostgreSQL
- Создаст таблицы при первом запуске

3. **Мигрируйте данные (если есть):**

Если у вас уже есть данные в SQLite:

```bash
# Скопируйте SQLite файл на сервер
scp neuromagic.db user@server:/path/to/project/

# На сервере выполните миграцию
docker-compose exec app python migrate_to_postgres.py
```

### Ручная установка PostgreSQL

Если не используете Docker:

```bash
# Установите PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Создайте пользователя и БД
sudo -u postgres psql
CREATE DATABASE neuromagic;
CREATE USER neuromagic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE neuromagic TO neuromagic_user;
\q

# Обновите .env
DATABASE_URL=postgresql+asyncpg://neuromagic_user:your_password@localhost:5432/neuromagic

# Запустите миграцию
python migrate_to_postgres.py

# Запустите приложение
python -m hypercorn main:app --bind 0.0.0.0:8000
```

## 🔙 Откат на SQLite (если нужно)

Если нужно вернуться на SQLite:

1. **Закомментируйте DATABASE_URL в `.env`:**

```env
# DATABASE_URL=postgresql+asyncpg://...
```

2. **Перезапустите приложение:**

```bash
docker-compose restart app
# или
python -m hypercorn main:app
```

Приложение автоматически вернётся к использованию SQLite.

## 📊 Мониторинг PostgreSQL

### Подключение к PostgreSQL

```bash
# Через Docker
docker-compose exec postgres psql -U neuromagic_user -d neuromagic

# Напрямую (если установлен psql)
psql postgresql://neuromagic_user:password@localhost:5432/neuromagic
```

### Полезные команды

```sql
-- Список таблиц
\dt

-- Структура таблицы
\d users

-- Количество пользователей
SELECT COUNT(*) FROM users;

-- Последние зарегистрированные
SELECT username, email, created_at FROM users ORDER BY created_at DESC LIMIT 10;

-- Размер базы данных
SELECT pg_size_pretty(pg_database_size('neuromagic'));
```

## 🔒 Бэкапы PostgreSQL

### Создание бэкапа

```bash
# Через Docker
docker-compose exec postgres pg_dump -U neuromagic_user neuromagic > backup_$(date +%Y%m%d).sql

# Напрямую
pg_dump -U neuromagic_user -h localhost neuromagic > backup.sql
```

### Восстановление из бэкапа

```bash
# Через Docker
cat backup.sql | docker-compose exec -T postgres psql -U neuromagic_user neuromagic

# Напрямую
psql -U neuromagic_user -h localhost neuromagic < backup.sql
```

## ⚠️ Важные замечания

1. **Пароли**: Используйте сильные пароли в production!
2. **Бэкапы**: Настройте автоматические бэкапы БД
3. **Мониторинг**: Следите за размером БД и производительностью
4. **SSL**: В production используйте SSL соединение с PostgreSQL

## 🐛 Troubleshooting

### PostgreSQL не запускается

```bash
# Проверьте логи
docker-compose logs postgres

# Проверьте порты
sudo netstat -tlnp | grep 5432
```

### Ошибка подключения

```bash
# Проверьте что PostgreSQL доступен
docker-compose exec postgres pg_isready -U neuromagic_user

# Проверьте переменные окружения
docker-compose exec app env | grep DATABASE
```

### Данные не мигрировались

```bash
# Проверьте что SQLite файл существует
ls -la neuromagic.db

# Запустите миграцию с логами
python migrate_to_postgres.py
```
