"""
Сервис для отправки email через SMTP.
Поддерживает Yandex, Gmail, Mail.ru и другие SMTP серверы.
"""
import os
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger


def generate_verification_code() -> str:
    """
    Генерирует 6-значный код верификации.

    Returns:
        str: 6-значный числовой код
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


async def send_verification_email(email: str, code: str, username: str = "") -> bool:
    """
    Отправляет email с кодом верификации.

    Args:
        email: Email получателя
        code: 6-значный код верификации
        username: Имя пользователя (опционально)

    Returns:
        bool: True если отправлено успешно, False в случае ошибки
    """
    try:
        # Получаем настройки SMTP из переменных окружения
        smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.ru")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)
        smtp_from_name = os.getenv("SMTP_FROM_NAME", "Нейромагия")

        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured in .env")
            return False

        # Создаем сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Код подтверждения регистрации на Нейромагии: {code}'
        msg['From'] = f'{smtp_from_name} <{smtp_from_email}>'
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
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            # STARTTLS соединение
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

        logger.info(f"Verification email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
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
