"""
Сервис для работы с OpenRouter API.
Используется для генерации контента курсов через GPT-4/5.
"""
import httpx
from typing import Dict, List, Optional, Any
from loguru import logger

from app.config import Settings


class OpenRouterService:
    """
    Сервис для работы с OpenRouter API.

    Позволяет делать запросы к различным AI моделям:
    - openai/gpt-4
    - openai/gpt-5-mini
    - anthropic/claude-3
    """

    def __init__(self, settings: Settings):
        """
        Инициализация сервиса OpenRouter.

        Args:
            settings: Настройки приложения с API ключом
        """
        self.settings = settings
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.site_url = "https://neuro-magic.ru"  # Для рейтингов на openrouter.ai
        self.site_name = "Neuromagic"  # Используем латиницу для HTTP headers

        if not self.api_key:
            logger.warning("OpenRouter API key not found in settings")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "openai/gpt-5-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Делает запрос к OpenRouter API для генерации текста.

        Args:
            messages: Список сообщений в формате OpenAI
                [{"role": "user", "content": "Привет!"}]
            model: Модель для использования (по умолчанию gpt-5-mini)
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            str: Сгенерированный текст или None в случае ошибки
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
            }

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            # Добавляем max_tokens если указан
            if max_tokens:
                payload["max_tokens"] = max_tokens

            # Делаем асинхронный запрос
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                # Извлекаем текст ответа
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"OpenRouter API request successful. Model: {model}, tokens: {data.get('usage', {})}")
                    return content
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenRouter: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to make OpenRouter API request: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "openai/gpt-5-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Упрощённый метод для генерации текста по промту.

        Args:
            prompt: Текст запроса пользователя
            system_prompt: Системный промт (опционально)
            model: Модель для использования
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            str: Сгенерированный текст или None
        """
        messages = []

        # Добавляем system prompt если есть
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Добавляем основной промт
        messages.append({
            "role": "user",
            "content": prompt
        })

        return await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def generate_text_with_reasoning(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Генерирует текст с использованием Gemini 3 Pro с reasoning.

        Args:
            prompt: Текст запроса пользователя
            system_prompt: Системный промт (опционально)
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            str: Сгенерированный текст или None
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
            }

            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })

            payload = {
                "model": "google/gemini-3-pro-preview",
                "messages": messages,
                "temperature": temperature,
                "extra_body": {"reasoning": {"enabled": True}}
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            async with httpx.AsyncClient(timeout=120.0) as client:  # Увеличенный timeout для reasoning
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"Gemini reasoning request successful. Tokens: {data.get('usage', {})}")
                    return content
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Gemini: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to make Gemini reasoning request: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def generate_image(
        self,
        prompt: str,
    ) -> Optional[str]:
        """
        Генерирует изображение с использованием Gemini 3 Pro Image Preview.

        Args:
            prompt: Описание изображения для генерации

        Returns:
            str: Base64 data URL изображения или None
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
            }

            payload = {
                "model": "google/gemini-3-pro-image-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "modalities": ["image", "text"]
            }

            async with httpx.AsyncClient(timeout=180.0) as client:  # Большой timeout для генерации изображений
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                # Извлекаем изображение из ответа
                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0]["message"]
                    if message.get("images"):
                        for image in message["images"]:
                            image_url = image["image_url"]["url"]  # Base64 data URL
                            logger.info("Image generated successfully with Gemini")
                            return image_url
                    else:
                        logger.warning("No images in Gemini response")
                        return None
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Gemini Image: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate image with Gemini: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# Глобальный экземпляр сервиса
_openrouter_service: Optional[OpenRouterService] = None


def get_openrouter_service() -> OpenRouterService:
    """
    Возвращает глобальный экземпляр OpenRouterService.

    Returns:
        OpenRouterService: Сервис для работы с OpenRouter API
    """
    global _openrouter_service
    if _openrouter_service is None:
        settings = Settings()
        _openrouter_service = OpenRouterService(settings)
    return _openrouter_service
