from __future__ import annotations

import os
from functools import cached_property

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    secret_key: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me-now"))
    site_name: str = "Нейромагия"
    contact_email: str = "hello@neuro-magic.ru"
    hero_video: str = "https://storage.yandexcloud.net/neuro-magic/hero-loop.mp4"
    accent_colors: tuple[str, ...] = ("#a855f7", "#38bdf8", "#f472b6")

    # ЮKassa настройки
    yookassa_shop_id: str = Field(default_factory=lambda: os.getenv("YOOKASSA_SHOP_ID", ""))
    yookassa_secret_key: str = Field(default_factory=lambda: os.getenv("YOOKASSA_SECRET_KEY", ""))
    yookassa_return_url: str = Field(default_factory=lambda: os.getenv("YOOKASSA_RETURN_URL", "https://neuro-magic.ru/payment/success"))

    # OpenRouter API (для AI генерации контента)
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))

    @cached_property
    def debug(self) -> bool:
        return self.app_env != "production"

