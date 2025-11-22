# SSL Setup Guide

Этот файл содержит инструкции по настройке SSL сертификатов для Нейромагии.

## Автоматическая настройка (рекомендуется)

На сервере выполните:

```bash
# 1. Перейдите в директорию проекта
cd /opt/neuromagic

# 2. Запустите скрипт настройки SSL
sudo bash setup-ssl.sh
```

Скрипт автоматически:
- ✅ Установит certbot (если не установлен)
- ✅ Получит SSL сертификаты от Let's Encrypt
- ✅ Скопирует сертификаты в nginx/ssl/
- ✅ Активирует HTTPS в nginx.conf
- ✅ Перезапустит Nginx
- ✅ Настроит автообновление сертификатов

## Ручная настройка

Если автоматический скрипт не работает, выполните вручную:

### Шаг 1: Установка Certbot

```bash
sudo apt-get update
sudo apt-get install -y certbot
```

### Шаг 2: Создание webroot директории

```bash
sudo mkdir -p /var/www/certbot
```

### Шаг 3: Получение сертификата

```bash
sudo certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email hello@neuro-magic.ru \
    --agree-tos \
    --no-eff-email \
    -d neuromagicai.ru \
    -d www.neuromagicai.ru
```

### Шаг 4: Копирование сертификатов

```bash
cd /opt/neuromagic
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/neuromagicai.ru/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/neuromagicai.ru/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

### Шаг 5: Активация HTTPS в nginx.conf

Откройте `nginx/nginx.conf` и раскомментируйте HTTPS блок (уберите `#` в начале строк):

```nginx
# Было:
#server {
#    listen 443 ssl http2;
#    ...
#}

# Стало:
server {
    listen 443 ssl http2;
    ...
}
```

### Шаг 6: Перезапуск Nginx

```bash
sudo docker-compose restart nginx
```

### Шаг 7: Проверка

Откройте в браузере:
- https://neuromagicai.ru
- https://www.neuromagicai.ru

## Автообновление сертификатов

Сертификаты Let's Encrypt действуют 90 дней. Для автообновления:

```bash
# Создайте скрипт обновления
sudo nano /usr/local/bin/renew-neuromagic-ssl.sh
```

Содержимое:
```bash
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/neuromagicai.ru/fullchain.pem /opt/neuromagic/nginx/ssl/
cp /etc/letsencrypt/live/neuromagicai.ru/privkey.pem /opt/neuromagic/nginx/ssl/
docker-compose -f /opt/neuromagic/docker-compose.yml restart nginx
```

Сделайте исполняемым:
```bash
sudo chmod +x /usr/local/bin/renew-neuromagic-ssl.sh
```

Добавьте в crontab (обновление каждые 12 часов):
```bash
sudo crontab -e
```

Добавьте строку:
```
0 */12 * * * /usr/local/bin/renew-neuromagic-ssl.sh >> /var/log/certbot-renew.log 2>&1
```

## Проблемы и решения

### Ошибка: "DNS resolution failed"
- Проверьте DNS записи домена
- A запись должна указывать на IP сервера
- Подождите распространения DNS (до 48 часов)

### Ошибка: "Connection refused"
- Проверьте что порт 80 открыт: `sudo ufw status`
- Проверьте что Nginx запущен: `docker-compose ps`

### Ошибка: "Too many certificates"
- Let's Encrypt лимит: 5 сертификатов на домен в неделю
- Используйте `--staging` для тестирования
- Подождите неделю для сброса лимита

### Nginx не запускается после активации HTTPS
- Проверьте логи: `docker-compose logs nginx`
- Проверьте права на сертификаты: `ls -la nginx/ssl/`
- Проверьте пути в nginx.conf

## Проверка сертификата

После настройки проверьте:

```bash
# Проверка срока действия
sudo certbot certificates

# Тест обновления
sudo certbot renew --dry-run

# Проверка SSL через браузер
# Откройте https://neuromagicai.ru и проверьте замок в адресной строке
```

## SSL Rating

Проверьте SSL конфигурацию на:
- https://www.ssllabs.com/ssltest/analyze.html?d=neuromagicai.ru

Должен быть рейтинг A или A+.
