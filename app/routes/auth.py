"""
Роуты для авторизации: регистрация, вход, выход, Telegram OAuth.
Использует Quart-Auth для управления сессиями.
"""
from quart import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import hashlib
import hmac
import os

from app.database import get_session
from app.models import User, EmailVerification
from app.schemas.auth import LoginForm, RegisterForm
from app.services.email import send_verification_email, generate_verification_code
from pydantic import ValidationError
from loguru import logger

bp = Blueprint("auth", __name__)


# ============================================
# TELEGRAM HASH VERIFICATION
# ============================================
def verify_telegram_auth(auth_data: dict) -> bool:
    """
    Верификация подлинности данных от Telegram Login Widget.

    Алгоритм согласно документации Telegram:
    https://core.telegram.org/widgets/login#checking-authorization

    Args:
        auth_data: Словарь с данными от Telegram (id, first_name, username, photo_url, auth_date, hash)

    Returns:
        bool: True если данные подлинные, False если поддельные
    """
    check_hash = auth_data.get('hash')
    if not check_hash:
        return False

    bot_token = os.getenv('TELEGRAM_OAUTH_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_OAUTH_BOT_TOKEN not configured")
        return False

    # Создаем копию данных без hash
    auth_data_copy = {k: v for k, v in auth_data.items() if k != 'hash'}

    # Сортируем по ключам и создаем строку data_check_string
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data_copy.items())]
    data_check_string = '\n'.join(data_check_arr)

    # Создаем secret_key = SHA256(bot_token)
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Вычисляем hash = HMAC_SHA256(data_check_string, secret_key)
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # Сравниваем с полученным hash
    return hmac.compare_digest(calculated_hash, check_hash)


# ============================================
# РЕГИСТРАЦИЯ (Шаг 1: Отправка кода)
# ============================================
@bp.route("/register", methods=["GET", "POST"])
async def register():
    """
    Форма регистрации нового пользователя.

    GET: отображает форму регистрации
    POST: валидирует данные и отправляет код подтверждения на email

    Двухэтапная регистрация:
    1. Ввод username, email, password → отправка кода
    2. Ввод кода → создание пользователя
    """
    if request.method == "GET":
        # Очищаем временные данные регистрации если есть
        session.pop("reg_data", None)
        return await render_template("auth/register.html", page_title="Регистрация")

    # Обработка POST запроса (Шаг 1)
    form_data = await request.form
    errors = []

    try:
        # Валидация данных формы
        form = RegisterForm(
            username=form_data.get("username", ""),
            email=form_data.get("email", ""),
            password=form_data.get("password", ""),
        )

        # Проверка наличия пользователя в БД
        async for db in get_session():
            # Проверка username
            result = await db.execute(select(User).where(User.username == form.username))
            if result.scalar_one_or_none():
                errors.append("Пользователь с таким именем уже существует")

            # Проверка email
            result = await db.execute(select(User).where(User.email == form.email))
            if result.scalar_one_or_none():
                errors.append("Пользователь с таким email уже существует")

            if errors:
                return await render_template(
                    "auth/register.html",
                    errors=errors,
                    form_data=form_data,
                    page_title="Регистрация"
                )

            # Генерация и отправка кода верификации
            code = generate_verification_code()

            # Удаляем старые коды для этого email
            await db.execute(
                delete(EmailVerification).where(EmailVerification.email == form.email)
            )

            # Сохраняем новый код в БД
            verification = EmailVerification(email=form.email, code=code)
            db.add(verification)
            await db.commit()

            # Отправляем email с кодом
            email_sent = await send_verification_email(form.email, code, form.username)

            if not email_sent:
                errors.append("Не удалось отправить код на почту. Возникли технические неполадки. Попробуйте позже.")
                return await render_template(
                    "auth/register.html",
                    errors=errors,
                    form_data=form_data,
                    page_title="Регистрация"
                )

            # Сохраняем данные в сессию для следующего шага
            session["reg_data"] = {
                "username": form.username,
                "email": form.email,
                "password": form.password
            }

            logger.info(f"Verification code sent to {form.email}")

            # Переходим к форме ввода кода
            return await render_template(
                "auth/register_verify.html",
                email=form.email,
                page_title="Подтверждение email"
            )

    except ValidationError as e:
        # Ошибки валидации Pydantic
        errors = [err["msg"] for err in e.errors()]
        return await render_template(
            "auth/register.html",
            errors=errors,
            form_data=form_data,
            page_title="Регистрация"
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        errors = [f"Ошибка регистрации: {str(e)}"]
        return await render_template(
            "auth/register.html",
            errors=errors,
            form_data=form_data,
            page_title="Регистрация"
        )


# ============================================
# РЕГИСТРАЦИЯ (Шаг 2: Проверка кода)
# ============================================
@bp.route("/register/verify", methods=["POST"])
async def register_verify():
    """
    Проверка кода верификации и создание пользователя.

    POST: принимает код, проверяет его и создаёт пользователя
    """
    form_data = await request.form
    code = form_data.get("code", "").strip()
    errors = []

    # Получаем данные из сессии
    reg_data = session.get("reg_data")
    if not reg_data:
        return redirect(url_for("auth.register"))

    email = reg_data["email"]

    try:
        async for db in get_session():
            # Ищем код верификации
            result = await db.execute(
                select(EmailVerification)
                .where(EmailVerification.email == email)
                .where(EmailVerification.is_verified == False)
                .order_by(EmailVerification.created_at.desc())
            )
            verification = result.scalar_one_or_none()

            if not verification:
                errors.append("Код верификации не найден. Запросите новый код.")
            elif verification.is_expired():
                errors.append("Код верификации истек. Запросите новый код.")
            elif verification.code != code:
                errors.append("Неверный код верификации")

            if errors:
                return await render_template(
                    "auth/register_verify.html",
                    errors=errors,
                    email=email,
                    page_title="Подтверждение email"
                )

            # Код верный, создаем пользователя
            new_user = User(
                username=reg_data["username"],
                email=reg_data["email"],
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={reg_data['username']}"
            )
            new_user.set_password(reg_data["password"])

            # Помечаем код как использованный
            verification.is_verified = True

            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            # Очищаем временные данные
            session.pop("reg_data", None)

            # Авторизация после регистрации
            session["user_id"] = new_user.id
            session["username"] = new_user.username
            session["avatar_url"] = new_user.avatar_url

            logger.info(f"User {new_user.username} successfully registered")

            return redirect(url_for("public.index"))

    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        errors = [f"Ошибка верификации: {str(e)}"]
        return await render_template(
            "auth/register_verify.html",
            errors=errors,
            email=email,
            page_title="Подтверждение email"
        )


# ============================================
# ПОВТОРНАЯ ОТПРАВКА КОДА
# ============================================
@bp.route("/register/resend", methods=["POST"])
async def register_resend():
    """
    Повторная отправка кода верификации.
    """
    reg_data = session.get("reg_data")
    if not reg_data:
        return jsonify({"success": False, "error": "Данные регистрации не найдены"}), 400

    email = reg_data["email"]
    username = reg_data["username"]

    try:
        async for db in get_session():
            # Генерируем новый код
            code = generate_verification_code()

            # Удаляем старые коды
            await db.execute(
                delete(EmailVerification).where(EmailVerification.email == email)
            )

            # Сохраняем новый код
            verification = EmailVerification(email=email, code=code)
            db.add(verification)
            await db.commit()

            # Отправляем email
            email_sent = await send_verification_email(email, code, username)

            if not email_sent:
                return jsonify({"success": False, "error": "Не удалось отправить email"}), 500

            logger.info(f"Verification code resent to {email}")
            return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Resend error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# ВХОД
# ============================================
@bp.route("/login", methods=["GET", "POST"])
async def login():
    """
    Форма входа в систему.
    
    GET: отображает форму входа
    POST: проверяет логин и пароль, создаёт сессию
    
    Логика:
    - поиск пользователя по username или email
    - проверка пароля
    - создание сессии
    """
    if request.method == "GET":
        return await render_template("auth/login.html", page_title="Вход")
    
    # Обработка POST запроса
    form_data = await request.form
    errors = []
    
    try:
        # Валидация данных
        form = LoginForm(
            username=form_data.get("username", ""),
            password=form_data.get("password", ""),
        )
        
        async for db in get_session():
            # Поиск пользователя (по username или email)
            result = await db.execute(
                select(User).where(
                    (User.username == form.username) | (User.email == form.username)
                )
            )
            user = result.scalar_one_or_none()
            
            # Проверка существования и пароля
            if not user:
                errors.append("Неверный логин или пароль")
            elif not user.check_password(form.password):
                errors.append("Неверный логин или пароль")
            elif not user.is_active:
                errors.append("Аккаунт деактивирован")
            else:
                # Успешная авторизация
                session["user_id"] = user.id
                session["username"] = user.username
                session["avatar_url"] = user.avatar_url
                
                return redirect(url_for("public.index"))
            
            if errors:
                return await render_template(
                    "auth/login.html",
                    errors=errors,
                    form_data=form_data,
                    page_title="Вход"
                )
    
    except ValidationError as e:
        errors = [err["msg"] for err in e.errors()]
        return await render_template(
            "auth/login.html",
            errors=errors,
            form_data=form_data,
            page_title="Вход"
        )
    except Exception as e:
        errors = [f"Ошибка входа: {str(e)}"]
        return await render_template(
            "auth/login.html",
            errors=errors,
            form_data=form_data,
            page_title="Вход"
        )


# ============================================
# ВЫХОД
# ============================================
@bp.route("/logout")
async def logout():
    """
    Выход из системы.
    Очищает сессию и редиректит на главную.
    """
    session.clear()
    return redirect(url_for("public.index"))


# ============================================
# TELEGRAM OAUTH
# ============================================
@bp.route("/telegram")
async def telegram_login():
    """
    OAuth через Telegram.

    Отображает страницу с Telegram Login Widget.
    Если TELEGRAM_OAUTH_BOT_USERNAME настроен, показывает виджет.
    Иначе показывает инструкции по настройке.

    Документация: https://core.telegram.org/widgets/login
    """
    bot_username = os.getenv("TELEGRAM_OAUTH_BOT_USERNAME")

    return await render_template(
        "auth/telegram.html",
        page_title="Вход через Telegram",
        bot_username=bot_username
    )


# ============================================
# CALLBACK ДЛЯ TELEGRAM
# ============================================
@bp.route("/telegram/callback")
async def telegram_callback():
    """
    Callback endpoint для Telegram OAuth.
    Принимает данные от Telegram Login Widget и создаёт/авторизует пользователя.

    Параметры от Telegram (GET query params):
    - id: Telegram user ID
    - first_name: имя
    - username: username в Telegram (опционально)
    - photo_url: URL аватара (опционально)
    - auth_date: timestamp авторизации
    - hash: подпись данных
    """
    # Telegram Login Widget отправляет данные через GET параметры
    auth_data = dict(request.args)

    if not auth_data or 'id' not in auth_data:
        logger.warning("Telegram callback called without required data")
        await flash("Ошибка авторизации через Telegram", "error")
        return redirect(url_for("auth.login"))

    # Верификация подлинности данных
    if not verify_telegram_auth(auth_data):
        logger.warning(f"Invalid Telegram auth data: {auth_data.get('id')}")
        await flash("Неверная подпись данных от Telegram. Попробуйте снова.", "error")
        return redirect(url_for("auth.login"))

    telegram_id = auth_data.get("id")
    telegram_username = auth_data.get("username")
    first_name = auth_data.get("first_name", "User")
    photo_url = auth_data.get("photo_url")

    try:
        async for db in get_session():
            # Поиск пользователя по telegram_id
            result = await db.execute(select(User).where(User.telegram_id == int(telegram_id)))
            user = result.scalar_one_or_none()

            if not user:
                # Проверяем, не занят ли username
                username = telegram_username or f"tg_{telegram_id}"
                result = await db.execute(select(User).where(User.username == username))
                if result.scalar_one_or_none():
                    # Username занят, добавляем ID
                    username = f"{username}_{telegram_id}"

                # Создание нового пользователя
                email = f"{telegram_id}@telegram.user"  # фиктивный email для Telegram пользователей

                user = User(
                    username=username,
                    email=email,
                    telegram_id=int(telegram_id),
                    telegram_username=telegram_username,
                    avatar_url=photo_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)

                logger.info(f"New user created via Telegram: {username} (TG ID: {telegram_id})")
            else:
                # Обновляем аватар и username если изменились в Telegram
                if photo_url and user.avatar_url != photo_url:
                    user.avatar_url = photo_url
                if telegram_username and user.telegram_username != telegram_username:
                    user.telegram_username = telegram_username
                await db.commit()

                logger.info(f"User logged in via Telegram: {user.username} (TG ID: {telegram_id})")

            # Авторизация
            session["user_id"] = user.id
            session["username"] = user.username
            session["avatar_url"] = user.avatar_url

            return redirect(url_for("public.index"))

    except Exception as e:
        logger.error(f"Telegram callback error: {str(e)}")
        await flash("Произошла ошибка при авторизации через Telegram", "error")
        return redirect(url_for("auth.login"))
