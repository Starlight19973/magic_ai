"""
Роуты для авторизации: регистрация, вход, выход, Telegram OAuth.
Использует Quart-Auth для управления сессиями.
"""
from quart import Blueprint, redirect, render_template, request, session, url_for, flash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.auth import LoginForm, RegisterForm
from pydantic import ValidationError

bp = Blueprint("auth", __name__)


# ============================================
# РЕГИСТРАЦИЯ
# ============================================
@bp.route("/register", methods=["GET", "POST"])
async def register():
    """
    Форма регистрации нового пользователя.
    
    GET: отображает форму регистрации
    POST: обрабатывает данные формы, создаёт пользователя
    
    Валидация:
    - проверка уникальности username и email
    - проверка корректности данных
    - хеширование пароля
    """
    if request.method == "GET":
        return await render_template("auth/register.html", page_title="Регистрация")
    
    # Обработка POST запроса
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
            
            # Создание нового пользователя
            new_user = User(
                username=form.username,
                email=form.email,
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={form.username}"
            )
            new_user.set_password(form.password)
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            # Авторизация после регистрации
            session["user_id"] = new_user.id
            session["username"] = new_user.username
            session["avatar_url"] = new_user.avatar_url
            
            return redirect(url_for("public.index"))
    
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
        errors = [f"Ошибка регистрации: {str(e)}"]
        return await render_template(
            "auth/register.html",
            errors=errors,
            form_data=form_data,
            page_title="Регистрация"
        )


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
# TELEGRAM OAUTH (заглушка для будущей реализации)
# ============================================
@bp.route("/telegram")
async def telegram_login():
    """
    OAuth через Telegram.
    
    TODO: Реализовать полную интеграцию с Telegram Login Widget:
    1. Получить bot token от BotFather
    2. Настроить Telegram Login Widget на фронтенде
    3. Верифицировать данные от Telegram (hash проверка)
    4. Создать или обновить пользователя с telegram_id
    
    Документация: https://core.telegram.org/widgets/login
    """
    return await render_template(
        "auth/telegram.html",
        page_title="Вход через Telegram"
    )


# ============================================
# CALLBACK ДЛЯ TELEGRAM
# ============================================
@bp.route("/telegram/callback", methods=["POST"])
async def telegram_callback():
    """
    Callback endpoint для Telegram OAuth.
    Принимает данные от Telegram Login Widget и создаёт/авторизует пользователя.
    
    Параметры от Telegram:
    - id: Telegram user ID
    - first_name: имя
    - username: username в Telegram (опционально)
    - photo_url: URL аватара (опционально)
    - auth_date: timestamp авторизации
    - hash: подпись данных
    
    TODO: Добавить проверку hash для безопасности
    """
    form_data = await request.form
    telegram_id = form_data.get("id")
    telegram_username = form_data.get("username")
    first_name = form_data.get("first_name", "User")
    photo_url = form_data.get("photo_url")
    
    if not telegram_id:
        return redirect(url_for("auth.login"))
    
    async for db in get_session():
        # Поиск пользователя по telegram_id
        result = await db.execute(select(User).where(User.telegram_id == int(telegram_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            # Создание нового пользователя
            username = telegram_username or f"tg_{telegram_id}"
            email = f"{telegram_id}@telegram.user"  # фиктивный email
            
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
        
        # Авторизация
        session["user_id"] = user.id
        session["username"] = user.username
        session["avatar_url"] = user.avatar_url
        
        return redirect(url_for("public.index"))
