"""
Middleware для проверки срока действия сессии.
Автоматически выходит из аккаунта если сессия истекла.
"""
from datetime import datetime, timedelta
from quart import session, redirect, url_for, request
from quart_auth import logout_user
from loguru import logger


# Длительность сессии
SESSION_LIFETIME_HOURS = 24


async def check_session_expiry():
    """
    Проверяет срок действия сессии перед каждым запросом.
    Если сессия истекла - выходит из аккаунта.
    """
    # Игнорируем проверку для статических файлов и роутов авторизации
    if request.path.startswith('/static/') or request.path.startswith('/auth/'):
        return
    
    # Проверяем наличие пользователя в сессии
    user_id = session.get('user_id')
    if not user_id:
        return
    
    # Проверяем время входа
    login_time_str = session.get('login_time')
    if not login_time_str:
        # Если login_time не установлен, устанавливаем сейчас (для обратной совместимости)
        session['login_time'] = datetime.utcnow().isoformat()
        return
    
    try:
        login_time = datetime.fromisoformat(login_time_str)
        now = datetime.utcnow()
        session_age = now - login_time
        
        # Проверяем, не истекла ли сессия
        if session_age > timedelta(hours=SESSION_LIFETIME_HOURS):
            logger.info(f"Session expired for user {user_id}. Age: {session_age}")
            logout_user()
            session.clear()
            # Сессия истекла, но мы не делаем редирект здесь,
            # просто очищаем данные. Шаблоны покажут форму входа.
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing login_time: {e}")
        # В случае ошибки парсинга, переустанавливаем время
        session['login_time'] = datetime.utcnow().isoformat()
