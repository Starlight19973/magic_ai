"""
Pydantic схемы для форм авторизации и регистрации.
Валидация данных от пользователя.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterForm(BaseModel):
    """
    Форма регистрации нового пользователя.
    
    Валидация:
    - username: 3-50 символов, только буквы, цифры, underscore
    - email: валидный email
    - password: минимум 6 символов
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Проверка что username содержит только допустимые символы"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username может содержать только буквы, цифры, _ и -')
        return v.lower()


class LoginForm(BaseModel):
    """
    Форма входа в систему.
    
    Поля:
    - username: логин или email
    - password: пароль
    """
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    """
    Схема ответа с данными пользователя (без sensitive данных).
    Используется для возврата информации о пользователе в API.
    """
    id: int
    username: str
    email: str
    avatar_url: str
    telegram_username: str | None = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

