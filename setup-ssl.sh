#!/bin/bash

# Скрипт для настройки SSL сертификатов через Let's Encrypt (Certbot)
# Автоматическая настройка HTTPS для домена neuromagicai.ru

set -e

echo "🔐 Настройка SSL сертификатов для Нейромагии"
echo "=============================================="

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка что скрипт запущен с правами sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Пожалуйста, запустите скрипт с sudo${NC}"
    exit 1
fi

# Переменные
DOMAIN="neuromagicai.ru"
WWW_DOMAIN="www.neuromagicai.ru"
EMAIL="hello@neuro-magic.ru"
SSL_DIR="./nginx/ssl"
WEBROOT="/var/www/certbot"

echo -e "${YELLOW}📋 Параметры:${NC}"
echo "  Домен: $DOMAIN"
echo "  WWW домен: $WWW_DOMAIN"
echo "  Email: $EMAIL"
echo "  SSL папка: $SSL_DIR"
echo ""

# Проверка установки certbot
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}📦 Certbot не установлен. Устанавливаем...${NC}"
    apt-get update
    apt-get install -y certbot
    echo -e "${GREEN}✅ Certbot установлен${NC}"
else
    echo -e "${GREEN}✅ Certbot уже установлен${NC}"
fi

# Создаём папку для webroot challenge
echo -e "${YELLOW}📁 Создаём папку для верификации...${NC}"
mkdir -p $WEBROOT
echo -e "${GREEN}✅ Папка создана: $WEBROOT${NC}"

# Проверка что Nginx запущен
echo -e "${YELLOW}🔍 Проверяем статус Docker контейнеров...${NC}"
if ! docker-compose ps | grep -q "neuromagic-nginx.*Up"; then
    echo -e "${RED}❌ Nginx контейнер не запущен. Запускаем...${NC}"
    docker-compose up -d nginx
    sleep 5
fi
echo -e "${GREEN}✅ Nginx запущен${NC}"

# Получение сертификата через webroot
echo -e "${YELLOW}🔐 Получаем SSL сертификат от Let's Encrypt...${NC}"
echo "  Это может занять несколько секунд..."
echo ""

certbot certonly \
    --webroot \
    --webroot-path=$WEBROOT \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN \
    -d $WWW_DOMAIN

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Сертификат успешно получен!${NC}"
else
    echo -e "${RED}❌ Ошибка получения сертификата${NC}"
    echo "Проверьте:"
    echo "  1. DNS записи настроены правильно"
    echo "  2. Порт 80 открыт"
    echo "  3. Домен доступен извне"
    exit 1
fi

# Копируем сертификаты в nginx/ssl
echo -e "${YELLOW}📋 Копируем сертификаты в проект...${NC}"
mkdir -p $SSL_DIR
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/
chmod 644 $SSL_DIR/fullchain.pem
chmod 600 $SSL_DIR/privkey.pem

echo -e "${GREEN}✅ Сертификаты скопированы${NC}"

# Раскомментирование HTTPS блока в nginx.conf
echo -e "${YELLOW}📝 Активируем HTTPS в nginx.conf...${NC}"

# Создаём backup
cp ./nginx/nginx.conf ./nginx/nginx.conf.backup

# Раскомментируем HTTPS блок (убираем #)
sed -i 's/^    #server {/    server {/' ./nginx/nginx.conf
sed -i 's/^    #    /    /' ./nginx/nginx.conf
sed -i 's/^    #}/    }/' ./nginx/nginx.conf

echo -e "${GREEN}✅ HTTPS активирован в конфигурации${NC}"

# Перезапуск Nginx
echo -e "${YELLOW}🔄 Перезапускаем Nginx...${NC}"
docker-compose restart nginx

# Ждём запуска
sleep 3

# Проверка статуса
if docker-compose ps | grep -q "neuromagic-nginx.*Up.*healthy"; then
    echo -e "${GREEN}✅ Nginx успешно перезапущен с HTTPS${NC}"
else
    echo -e "${RED}⚠️  Nginx перезапущен, но пока не healthy. Проверьте логи:${NC}"
    echo "  docker-compose logs nginx"
fi

# Настройка автообновления сертификатов
echo -e "${YELLOW}⏰ Настраиваем автообновление сертификатов...${NC}"

# Создаём cron job для автообновления
CRON_SCRIPT="/usr/local/bin/renew-neuromagic-ssl.sh"
cat > $CRON_SCRIPT << 'EOF'
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/neuromagicai.ru/fullchain.pem /opt/neuromagic/nginx/ssl/
cp /etc/letsencrypt/live/neuromagicai.ru/privkey.pem /opt/neuromagic/nginx/ssl/
docker-compose -f /opt/neuromagic/docker-compose.yml restart nginx
EOF

chmod +x $CRON_SCRIPT

# Добавляем в crontab (обновление каждые 12 часов)
(crontab -l 2>/dev/null | grep -v "renew-neuromagic-ssl"; echo "0 */12 * * * $CRON_SCRIPT >> /var/log/certbot-renew.log 2>&1") | crontab -

echo -e "${GREEN}✅ Автообновление настроено (каждые 12 часов)${NC}"

echo ""
echo -e "${GREEN}🎉 SSL сертификаты успешно настроены!${NC}"
echo ""
echo "Ваш сайт теперь доступен по HTTPS:"
echo "  • https://$DOMAIN"
echo "  • https://$WWW_DOMAIN"
echo ""
echo "Сертификаты будут автоматически обновляться."
echo "Срок действия: 90 дней"
echo ""
echo -e "${YELLOW}📝 Проверьте сайт в браузере!${NC}"
