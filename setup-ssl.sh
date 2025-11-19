#!/bin/bash

# Скрипт для настройки SSL сертификата Let's Encrypt

set -e

echo "🔐 Настройка SSL для Нейромагии"
echo ""

# Проверка что скрипт запущен с root правами
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Пожалуйста, запустите скрипт от root: sudo ./setup-ssl.sh"
    exit 1
fi

# Запрос домена
read -p "Введите ваш домен (например, neuro-magic.ru): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Домен не указан!"
    exit 1
fi

echo ""
echo "📝 Домен: $DOMAIN"
echo "📝 С www: www.$DOMAIN"
echo ""

# Подтверждение
read -p "Продолжить? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Отменено"
    exit 0
fi

echo ""
echo "📦 Установка Certbot..."

# Установка certbot
apt update
apt install -y certbot

echo ""
echo "🛑 Временная остановка nginx для получения сертификата..."

# Останавливаем nginx контейнер
cd /opt/neuromagic
docker-compose stop nginx

echo ""
echo "🔐 Получение SSL сертификата от Let's Encrypt..."

# Получаем сертификат
certbot certonly --standalone \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --non-interactive \
    --agree-tos \
    --email hello@$DOMAIN \
    --keep-until-expiring

echo ""
echo "📋 Копирование сертификатов в проект..."

# Создаём директорию для сертификатов
mkdir -p /opt/neuromagic/nginx/ssl

# Копируем сертификаты
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/neuromagic/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/neuromagic/nginx/ssl/

# Устанавливаем права
chmod 644 /opt/neuromagic/nginx/ssl/*.pem

echo ""
echo "⚙️  Обновление nginx конфигурации..."

# Обновляем конфиг nginx (заменяем YOUR_DOMAIN на реальный домен)
sed -i "s/YOUR_DOMAIN/$DOMAIN/g" /opt/neuromagic/nginx/nginx.conf

echo ""
echo "🚀 Перезапуск nginx..."

# Запускаем nginx обратно
cd /opt/neuromagic
docker-compose --profile production up -d nginx

echo ""
echo "⏰ Настройка автообновления сертификата..."

# Создаём скрипт для обновления
cat > /etc/cron.daily/renew-ssl << 'CRON_SCRIPT'
#!/bin/bash
certbot renew --quiet --deploy-hook "
    cp /etc/letsencrypt/live/*/fullchain.pem /opt/neuromagic/nginx/ssl/
    cp /etc/letsencrypt/live/*/privkey.pem /opt/neuromagic/nginx/ssl/
    cd /opt/neuromagic && docker-compose restart nginx
"
CRON_SCRIPT

chmod +x /etc/cron.daily/renew-ssl

echo ""
echo "✅ SSL настроен успешно!"
echo ""
echo "🌐 Ваш сайт доступен по адресу:"
echo "   https://$DOMAIN"
echo "   https://www.$DOMAIN"
echo ""
echo "📋 Сертификат будет автоматически обновляться каждый день"
echo ""
echo "🔍 Проверка конфигурации:"
docker-compose ps

echo ""
echo "✨ Готово!"

