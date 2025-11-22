"""
Утилиты для защиты от подбора паролей (rate limiting).
"""
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models import LoginAttempt


# Настройки rate limiting
MAX_LOGIN_ATTEMPTS = 5  # Максимум попыток
BLOCK_DURATION_MINUTES = 15  # Длительность блокировки в минутах
RESET_ATTEMPTS_MINUTES = 30  # Сбросить счетчик через N минут после последней попытки


async def check_rate_limit(db: AsyncSession, identifier: str) -> tuple[bool, str | None]:
    """
    Проверяет, не заблокирован ли пользователь.
    
    Args:
        db: Сессия БД
        identifier: Идентификатор (IP адрес или username)
    
    Returns:
        Tuple (is_allowed, error_message)
        - is_allowed: True если можно попытаться войти, False если заблокирован
        - error_message: Сообщение об ошибке если заблокирован
    """
    result = await db.execute(
        select(LoginAttempt).where(LoginAttempt.identifier == identifier)
    )
    attempt = result.scalar_one_or_none()
    
    now = datetime.utcnow()
    
    if not attempt:
        # Первая попытка
        return True, None
    
    # Проверяем, не истекла ли блокировка
    if attempt.is_blocked and attempt.blocked_until:
        if now >= attempt.blocked_until:
            # Блокировка истекла, разблокируем
            attempt.is_blocked = False
            attempt.attempts = 0
            attempt.blocked_until = None
            await db.commit()
            logger.info(f"Rate limit unblocked for {identifier}")
            return True, None
        else:
            # Все еще заблокирован
            minutes_left = int((attempt.blocked_until - now).total_seconds() / 60)
            return False, f"Слишком много попыток входа. Попробуйте через {minutes_left} минут."
    
    # Проверяем, не нужно ли сбросить счетчик
    time_since_last = now - attempt.last_attempt_at
    if time_since_last > timedelta(minutes=RESET_ATTEMPTS_MINUTES):
        attempt.attempts = 0
        await db.commit()
        logger.info(f"Rate limit reset for {identifier}")
        return True, None
    
    # Проверяем количество попыток
    if attempt.attempts >= MAX_LOGIN_ATTEMPTS:
        # Блокируем
        attempt.is_blocked = True
        attempt.blocked_until = now + timedelta(minutes=BLOCK_DURATION_MINUTES)
        await db.commit()
        logger.warning(f"Rate limit exceeded for {identifier}. Blocked for {BLOCK_DURATION_MINUTES} minutes.")
        return False, f"Слишком много попыток входа. Попробуйте через {BLOCK_DURATION_MINUTES} минут."
    
    return True, None


async def record_failed_login(db: AsyncSession, identifier: str) -> None:
    """
    Записывает неудачную попытку входа.
    
    Args:
        db: Сессия БД
        identifier: Идентификатор (IP адрес или username)
    """
    result = await db.execute(
        select(LoginAttempt).where(LoginAttempt.identifier == identifier)
    )
    attempt = result.scalar_one_or_none()
    
    now = datetime.utcnow()
    
    if not attempt:
        # Создаем новую запись
        attempt = LoginAttempt(
            identifier=identifier,
            attempts=1,
            last_attempt_at=now
        )
        db.add(attempt)
    else:
        # Увеличиваем счетчик
        attempt.attempts += 1
        attempt.last_attempt_at = now
    
    await db.commit()
    logger.info(f"Failed login recorded for {identifier}. Total attempts: {attempt.attempts}")


async def reset_login_attempts(db: AsyncSession, identifier: str) -> None:
    """
    Сбрасывает счетчик попыток после успешного входа.
    
    Args:
        db: Сессия БД
        identifier: Идентификатор (IP адрес или username)
    """
    result = await db.execute(
        select(LoginAttempt).where(LoginAttempt.identifier == identifier)
    )
    attempt = result.scalar_one_or_none()
    
    if attempt:
        attempt.attempts = 0
        attempt.is_blocked = False
        attempt.blocked_until = None
        await db.commit()
        logger.info(f"Login attempts reset for {identifier}")
