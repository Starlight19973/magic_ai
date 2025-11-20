"""
Сервис для отправки email через SMTP.
Поддерживает Yandex, Gmail, Mail.ru и другие SMTP серверы.
"""
import os
import smtplib
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger

# Thread pool для выполнения синхронных SMTP операций
_executor = ThreadPoolExecutor(max_workers=3)


def generate_verification_code() -> str:
    """
    Генерирует 6-значный код верификации.

    Returns:
        str: 6-значный числовой код
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def _send_email_sync(email: str, code: str, username: str = "") -> bool:
    """
    Синхронная функция отправки email.
    Вызывается из async функции через ThreadPoolExecutor.
    """
    try:
        # Получаем настройки SMTP из переменных окружения
        smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.ru")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_name = os.getenv("SMTP_FROM_NAME", "Нейромагия")
        # ВАЖНО: From должен точно совпадать с smtp_user для Яндекса
        smtp_from_email = smtp_user

        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured in .env")
            return False

        # Создаем сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Код подтверждения регистрации на Нейромагии: {code}'
        # Яндекс требует простой формат From без имени отправителя
        msg['From'] = smtp_from_email
        msg['To'] = email

        # HTML версия письма
        html_body = _get_email_html_template(code, username)

        # Текстовая версия (запасной вариант)
        text_body = f"""
Добро пожаловать в Нейромагию!

Ваш код подтверждения: {code}

Код действителен в течение 10 минут.

Если вы не регистрировались на сайте Нейромагия, просто проигнорируйте это письмо.

---
С уважением,
Команда Нейромагия
https://neuromagicai.ru
        """

        # Прикрепляем обе версии
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        # Отправляем письмо
        if smtp_port == 465:
            # SSL соединение
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.set_debuglevel(0)
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            # STARTTLS соединение (порт 587 или 25)
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.set_debuglevel(0)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

        logger.info(f"Verification email sent to {email}")
        return True

    except Exception as e:
        error_msg = f"Failed to send email to {email}: {str(e)}"
        logger.error(error_msg)
        print(f"[EMAIL ERROR] {error_msg}")  # Вывод в консоль
        print(f"[EMAIL ERROR] Exception type: {type(e).__name__}")
        print(f"[EMAIL ERROR] SMTP settings: host={smtp_host}, port={smtp_port}, user={smtp_user}")
        import traceback
        traceback.print_exc()  # Полный traceback в консоль
        return False


def _get_email_html_template(code: str, username: str = "") -> str:
    """
    Генерирует красивый HTML шаблон письма с кодом верификации.

    Args:
        code: 6-значный код верификации
        username: Имя пользователя

    Returns:
        str: HTML контент письма
    """
    greeting = f"Здравствуйте, {username}!" if username else "Здравствуйте!"

    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Код подтверждения</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
    <table width="100%" cellpadding="0" cellspacing="0" style="min-height: 100vh;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Главный контейнер -->
                <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden;">
                    <!-- Шапка с градиентом -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                ✨ Нейромагия
                            </h1>
                            <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                Магия искусственного интеллекта
                            </p>
                        </td>
                    </tr>

                    <!-- Основной контент -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1a202c; font-size: 24px; font-weight: 600;">
                                {greeting}
                            </h2>

                            <p style="margin: 0 0 30px; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Спасибо за регистрацию на платформе <strong>Нейромагия</strong>!
                                Чтобы подтвердить свой email, введите код ниже:
                            </p>

                            <!-- Код верификации -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 30px 0;">
                                        <div style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 3px;">
                                            <div style="background: white; border-radius: 10px; padding: 20px 40px;">
                                                <span style="font-size: 42px; font-weight: 700; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                                    {code}
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 30px 0 0; color: #718096; font-size: 14px; line-height: 1.6;">
                                ⏰ Код действителен в течение <strong>10 минут</strong>
                            </p>

                            <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #e2e8f0;">
                                <p style="margin: 0 0 10px; color: #718096; font-size: 14px;">
                                    Если вы не регистрировались на сайте Нейромагия, просто проигнорируйте это письмо.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Подвал -->
                    <tr>
                        <td style="background: #f7fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 10px; color: #4a5568; font-size: 14px;">
                                С уважением,<br>
                                <strong>Команда Нейромагия</strong>
                            </p>
                            <p style="margin: 15px 0 0; color: #a0aec0; font-size: 12px;">
                                <a href="https://neuromagicai.ru" style="color: #667eea; text-decoration: none;">neuromagicai.ru</a> •
                                <a href="mailto:hello@neuro-magic.ru" style="color: #667eea; text-decoration: none;">hello@neuro-magic.ru</a>
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Копирайт -->
                <p style="margin-top: 30px; color: rgba(255,255,255,0.8); font-size: 12px; text-align: center;">
                    © 2025 Нейромагия. Все права защищены.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
    """


async def send_verification_email(email: str, code: str, username: str = "") -> bool:
    """
    Async обертка для отправки email с кодом верификации.
    Выполняет синхронную SMTP операцию в отдельном потоке.

    Args:
        email: Email получателя
        code: 6-значный код верификации
        username: Имя пользователя (опционально)

    Returns:
        bool: True если отправлено успешно, False в случае ошибки
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _send_email_sync, email, code, username)


def _send_purchase_email_sync(email: str, username: str, course_title: str, course_id: str, amount: float) -> bool:
    """
    Синхронная функция отправки email о покупке курса.
    Вызывается из async функции через ThreadPoolExecutor.
    """
    try:
        # Получаем настройки SMTP из переменных окружения
        smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.ru")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_email = smtp_user

        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured in .env")
            return False

        # Создаем сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Вы приобрели курс "{course_title}" на Нейромагии!'
        msg['From'] = smtp_from_email
        msg['To'] = email

        # HTML версия письма
        html_body = _get_purchase_email_html_template(username, course_title, course_id, amount)

        # Текстовая версия (запасной вариант)
        text_body = f"""
Поздравляем, {username}!

Вы успешно приобрели курс "{course_title}" на платформе Нейромагия!

Сумма покупки: {amount:.2f} руб.

Что дальше?
1. Войдите в личный кабинет на сайте neuromagicai.ru
2. Перейдите в раздел "Мои курсы"
3. Начните обучение прямо сейчас!

Чек об оплате был отправлен на ваш email отдельным письмом.

Если у вас возникнут вопросы, пишите нам на hello@neuro-magic.ru

---
С уважением,
Команда Нейромагия
https://neuromagicai.ru
        """

        # Прикрепляем обе версии
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        # Отправляем письмо
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.set_debuglevel(0)
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.set_debuglevel(0)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

        logger.info(f"Purchase confirmation email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send purchase email to {email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def _get_purchase_email_html_template(username: str, course_title: str, course_id: str, amount: float) -> str:
    """
    Генерирует красивый HTML шаблон письма о покупке курса.

    Args:
        username: Имя пользователя
        course_title: Название курса
        course_id: ID курса
        amount: Сумма покупки

    Returns:
        str: HTML контент письма
    """
    # Определяем что пользователь получит в курсе (можно расширить)
    course_benefits = {
        "chatgpt-basics": [
            "10+ видео-уроков о работе с ChatGPT",
            "Практические задания и примеры",
            "Готовые шаблоны промптов",
            "Сертификат о прохождении курса"
        ],
        "prompt-engineering": [
            "15+ уроков по промпт-инжинирингу",
            "Продвинутые техники работы с AI",
            "Библиотека из 100+ промптов",
            "Сертификат о прохождении курса"
        ],
        "midjourney-master": [
            "20+ уроков по Midjourney",
            "Создание профессиональных изображений",
            "Секретные параметры и настройки",
            "Сертификат о прохождении курса"
        ],
    }

    benefits = course_benefits.get(course_id, [
        "Доступ к видео-урокам",
        "Практические задания",
        "Поддержка преподавателя",
        "Сертификат о прохождении"
    ])

    benefits_html = "".join([f"<li style='margin: 10px 0; color: #4a5568; font-size: 16px;'>✓ {benefit}</li>" for benefit in benefits])

    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Покупка курса</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
    <table width="100%" cellpadding="0" cellspacing="0" style="min-height: 100vh;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Главный контейнер -->
                <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden;">
                    <!-- Шапка с градиентом -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                🎉 Поздравляем!
                            </h1>
                            <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9); font-size: 18px;">
                                Вы приобрели курс на Нейромагии
                            </p>
                        </td>
                    </tr>

                    <!-- Основной контент -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 10px; color: #1a202c; font-size: 24px; font-weight: 600;">
                                Здравствуйте, {username}!
                            </h2>

                            <p style="margin: 0 0 30px; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Спасибо за покупку! Вы успешно приобрели курс:
                            </p>

                            <!-- Карточка курса -->
                            <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border-radius: 12px; padding: 25px; margin: 0 0 30px;">
                                <h3 style="margin: 0 0 10px; color: #667eea; font-size: 20px; font-weight: 600;">
                                    {course_title}
                                </h3>
                                <p style="margin: 0; color: #718096; font-size: 16px;">
                                    Сумма покупки: <strong style="color: #667eea;">{amount:.2f} руб.</strong>
                                </p>
                            </div>

                            <!-- Что вас ждет -->
                            <h3 style="margin: 0 0 20px; color: #1a202c; font-size: 20px; font-weight: 600;">
                                🚀 Что вас ждет:
                            </h3>
                            <ul style="margin: 0 0 30px; padding: 0 0 0 20px; list-style: none;">
                                {benefits_html}
                            </ul>

                            <!-- Как начать -->
                            <div style="background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 8px; padding: 20px; margin: 0 0 30px;">
                                <h4 style="margin: 0 0 15px; color: #065f46; font-size: 18px; font-weight: 600;">
                                    📚 Как начать обучение:
                                </h4>
                                <ol style="margin: 0; padding: 0 0 0 20px; color: #065f46;">
                                    <li style="margin: 8px 0;">Войдите в личный кабинет на <a href="https://neuromagicai.ru" style="color: #667eea; text-decoration: none;">neuromagicai.ru</a></li>
                                    <li style="margin: 8px 0;">Перейдите в раздел "Мои курсы"</li>
                                    <li style="margin: 8px 0;">Начните обучение прямо сейчас!</li>
                                </ol>
                            </div>

                            <!-- Кнопка -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="https://neuromagicai.ru/courses/{course_id}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
                                            Начать обучение →
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <div style="margin-top: 30px; padding-top: 25px; border-top: 2px solid #e2e8f0;">
                                <p style="margin: 0 0 10px; color: #718096; font-size: 14px;">
                                    📧 Чек об оплате был отправлен на ваш email отдельным письмом от ЮKassa.
                                </p>
                                <p style="margin: 10px 0 0; color: #718096; font-size: 14px;">
                                    💬 Если у вас возникнут вопросы, пишите нам на <a href="mailto:hello@neuro-magic.ru" style="color: #667eea; text-decoration: none;">hello@neuro-magic.ru</a>
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Подвал -->
                    <tr>
                        <td style="background: #f7fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 10px; color: #4a5568; font-size: 14px;">
                                С уважением,<br>
                                <strong>Команда Нейромагия</strong>
                            </p>
                            <p style="margin: 15px 0 0; color: #a0aec0; font-size: 12px;">
                                <a href="https://neuromagicai.ru" style="color: #667eea; text-decoration: none;">neuromagicai.ru</a> •
                                <a href="mailto:hello@neuro-magic.ru" style="color: #667eea; text-decoration: none;">hello@neuro-magic.ru</a>
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Копирайт -->
                <p style="margin-top: 30px; color: rgba(255,255,255,0.8); font-size: 12px; text-align: center;">
                    © 2025 Нейромагия. Все права защищены.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
    """


async def send_purchase_email(email: str, username: str, course_title: str, course_id: str, amount: float) -> bool:
    """
    Async обертка для отправки email о покупке курса.
    Выполняет синхронную SMTP операцию в отдельном потоке.

    Args:
        email: Email получателя
        username: Имя пользователя
        course_title: Название курса
        course_id: ID курса
        amount: Сумма покупки в рублях

    Returns:
        bool: True если отправлено успешно, False в случае ошибки
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _send_purchase_email_sync, email, username, course_title, course_id, amount)
