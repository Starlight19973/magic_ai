# 🤖 Настройка Telegram OAuth для Нейромагии

## Шаг 1: Создание бота

1. Откройте Telegram и найдите **@BotFather**
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: `Нейромагия Auth Bot`)
   - Введите username бота (должен заканчиваться на `bot`, например: `neuromagic_auth_bot`)
4. Сохраните полученный **Bot Token** (например: `123456:ABC-DEF1234...`)

## Шаг 2: Настройка домена

1. В BotFather отправьте `/setdomain`
2. Выберите своего бота
3. Укажите домен вашего сайта (например: `neuromagic.ru` или `127.0.0.1:5000` для локальной разработки)

## Шаг 3: Добавление Bot Token в .env

Откройте файл `.env` и добавьте:

```env
TELEGRAM_BOT_TOKEN=ВАШ_BOT_TOKEN_ЗДЕСЬ
```

## Шаг 4: Обновление шаблона

Откройте `templates/auth/telegram.html` и раскомментируйте Telegram Login Widget:

```html
<script async src="https://telegram.org/js/telegram-widget.js?22" 
        data-telegram-login="ИМЯ_ВАШЕГО_БОТА" 
        data-size="large" 
        data-auth-url="http://ВАШ_ДОМЕН/auth/telegram/callback"
        data-request-access="write">
</script>
```

Замените:
- `ИМЯ_ВАШЕГО_БОТА` на username вашего бота (без @)
- `http://ВАШ_ДОМЕН` на ваш реальный домен

## Шаг 5: Верификация данных (для production)

В файле `app/routes/auth.py` функция `telegram_callback` закомментирована строка:

```python
# TODO: Добавить проверку hash для безопасности
```

Для production необходимо добавить проверку подписи данных:

```python
import hashlib
import hmac

def verify_telegram_authentication(data: dict, bot_token: str) -> bool:
    """Проверяет подлинность данных от Telegram"""
    check_hash = data.pop('hash', None)
    if not check_hash:
        return False
    
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(data.items())
    )
    
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return expected_hash == check_hash
```

## Шаг 6: Тестирование

1. Запустите сервер: `python -m quart --app main:app --debug run`
2. Откройте http://127.0.0.1:5000/auth/telegram
3. Нажмите на виджет Telegram Login
4. Авторизуйтесь через Telegram
5. Вы будете перенаправлены на главную страницу с активной сессией

## Полезные ссылки

- [Telegram Login Widget Documentation](https://core.telegram.org/widgets/login)
- [Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)

## Примечания

- Для локальной разработки можно использовать `ngrok` для проброса localhost
- Telegram Login Widget работает только на HTTPS (кроме localhost)
- Обязательно добавьте проверку hash в production!

