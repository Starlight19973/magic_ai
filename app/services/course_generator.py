"""
Сервис для генерации контента курсов через AI.
Использует OpenRouter API (GPT-4/5) для создания уроков, квизов, и другого контента.
"""
import json
from typing import Dict, List, Optional
from loguru import logger

from app.services.openrouter import get_openrouter_service
from app.models import CourseModule, Lesson
from app.database import AsyncSessionLocal
from app.data.courses import COURSES_EXTENDED


class CourseGeneratorService:
    """
    Сервис для генерации контента курсов через AI.

    Генерирует:
    - Текстовый контент уроков (Markdown)
    - Квизы для проверки знаний
    - Описания модулей
    """

    def __init__(self):
        """Инициализация генератора курсов"""
        self.openrouter = get_openrouter_service()

    async def generate_lesson_content(
        self,
        lesson_title: str,
        module_title: str,
        course_title: str,
        target_audience: str = "начинающие",
        duration_minutes: int = 15,
    ) -> Dict[str, any]:
        """
        Генерирует контент для одного урока.

        Args:
            lesson_title: Название урока
            module_title: Название модуля (главы)
            course_title: Название курса
            target_audience: Целевая аудитория
            duration_minutes: Желаемая длительность урока

        Returns:
            dict: {"content_text": "...", "quiz_questions": {...}}
        """
        logger.info(f"Generating lesson content: {lesson_title}")

        # System prompt для генерации урока
        system_prompt = """Ты - опытный преподаватель курсов по искусственному интеллекту и нейросетям.
Твоя задача - создавать качественные, понятные и интересные уроки для студентов.

Требования к урокам:
- Используй простой и понятный язык
- Добавляй практические примеры
- Структурируй текст с заголовками и списками
- Используй Markdown форматирование
- Добавляй emoji для визуального разделения секций
- Длина урока: примерно {duration} минут чтения (около {words} слов)
- Заканчивай урок кратким резюме ключевых моментов

Структура урока:
1. 🎯 Введение (зачем это нужно)
2. 📚 Основной материал (теория + примеры)
3. 💡 Практические советы
4. ✨ Резюме ключевых моментов"""

        # User prompt с конкретной задачей
        user_prompt = f"""Создай урок для курса "{course_title}".

Модуль: {module_title}
Урок: {lesson_title}
Целевая аудитория: {target_audience}
Желаемая длительность: {duration_minutes} минут

Создай подробный, практический и интересный урок в формате Markdown.
Используй примеры из реальной жизни и практические кейсы."""

        # Генерируем текст урока с помощью Gemini с reasoning
        lesson_text = await self.openrouter.generate_text_with_reasoning(
            prompt=user_prompt,
            system_prompt=system_prompt.format(
                duration=duration_minutes,
                words=duration_minutes * 150  # ~150 слов в минуту
            ),
            temperature=0.7,
            max_tokens=8000  # Увеличено для более подробного контента
        )

        if not lesson_text:
            logger.error(f"Failed to generate lesson content for: {lesson_title}")
            return {
                "content_text": f"# {lesson_title}\n\nКонтент не сгенерирован. Попробуйте позже.",
                "quiz_questions": None
            }

        # Генерируем квиз для урока
        quiz_questions = await self.generate_quiz(lesson_title, lesson_text)

        return {
            "content_text": lesson_text,
            "quiz_questions": quiz_questions
        }

    async def generate_quiz(
        self,
        lesson_title: str,
        lesson_content: str,
    ) -> Optional[dict]:
        """
        Генерирует квиз для проверки знаний после урока.

        Args:
            lesson_title: Название урока
            lesson_content: Текст урока

        Returns:
            dict: Квиз в формате JSON или None
        """
        logger.info(f"Generating quiz for lesson: {lesson_title}")

        system_prompt = """Ты - эксперт по созданию образовательных квизов.
Твоя задача - создать тест для проверки знаний студента после урока.

Требования к квизу:
- 5 вопросов на понимание материала
- 4 варианта ответа на каждый вопрос
- Только один правильный ответ
- Вопросы должны проверять понимание, а не запоминание
- Ответы должны быть примерно одинаковой длины

Формат ответа - строго JSON:
{
    "questions": [
        {
            "question": "Текст вопроса?",
            "answers": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
            "correct": 0,
            "explanation": "Краткое объяснение правильного ответа"
        }
    ]
}"""

        user_prompt = f"""Создай квиз из 5 вопросов для урока "{lesson_title}".

Контент урока:
{lesson_content[:2000]}...

Верни ТОЛЬКО валидный JSON без дополнительного текста."""

        # Генерируем квиз с помощью Gemini с reasoning
        quiz_text = await self.openrouter.generate_text_with_reasoning(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=3000
        )

        if not quiz_text:
            logger.warning(f"Failed to generate quiz for: {lesson_title}")
            return None

        try:
            # Очищаем текст от markdown кодблоков если есть
            quiz_text = quiz_text.strip()
            if quiz_text.startswith("```json"):
                quiz_text = quiz_text.replace("```json", "").replace("```", "").strip()
            elif quiz_text.startswith("```"):
                quiz_text = quiz_text.replace("```", "").strip()

            # Парсим JSON
            quiz_data = json.loads(quiz_text)
            logger.info(f"Quiz generated successfully for: {lesson_title}")
            return quiz_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz JSON: {e}\nText: {quiz_text}")
            return None

    async def generate_course(
        self,
        course_slug: str,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Генерирует полный контент для курса (все модули и уроки).

        Args:
            course_slug: Slug курса (например "ai-for-beginners")
            progress_callback: Функция для отслеживания прогресса (опционально)

        Returns:
            bool: True если успешно, False если ошибка
        """
        logger.info(f"Starting course generation for: {course_slug}")

        # Получаем данные курса из каталога
        course_data = COURSES_EXTENDED.get(course_slug)
        if not course_data:
            logger.error(f"Course not found in catalog: {course_slug}")
            return False

        # Получаем информацию о курсе
        from app.data.catalog import COURSES
        course_info = next((c for c in COURSES if c.slug == course_slug), None)
        if not course_info:
            logger.error(f"Course info not found: {course_slug}")
            return False

        try:
            async with AsyncSessionLocal() as session:
                # Удаляем старые модули если есть (для повторной генерации)
                from sqlalchemy import select, delete
                existing_modules = await session.execute(
                    select(CourseModule).where(CourseModule.course_slug == course_slug)
                )
                for module in existing_modules.scalars():
                    await session.delete(module)
                await session.commit()

                # Генерируем каждый модуль
                total_lessons = 0
                generated_lessons = 0

                for module_order, module_data in enumerate(course_data["program"], start=1):
                    # Создаём модуль
                    course_module = CourseModule(
                        course_slug=course_slug,
                        order=module_order,
                        title=module_data["title"],
                        description=f"Модуль {module_order} курса {course_info.title}"
                    )
                    session.add(course_module)
                    await session.flush()  # Чтобы получить ID модуля

                    logger.info(f"Created module: {course_module.title}")

                    # Генерируем уроки для модуля
                    for lesson_order, lesson_title in enumerate(module_data["lessons"], start=1):
                        total_lessons += 1

                        # Callback для прогресса
                        if progress_callback:
                            progress_callback(generated_lessons, total_lessons, lesson_title)

                        # Генерируем контент урока
                        lesson_content = await self.generate_lesson_content(
                            lesson_title=lesson_title,
                            module_title=module_data["title"],
                            course_title=course_info.title,
                            target_audience=course_info.level,
                            duration_minutes=15
                        )

                        # Создаём урок в БД
                        lesson = Lesson(
                            module_id=course_module.id,
                            order=lesson_order,
                            title=lesson_title,
                            content_type="text",
                            content_text=lesson_content["content_text"],
                            quiz_questions=lesson_content["quiz_questions"],
                            estimated_time_minutes=15,
                            is_free=(lesson_order == 1)  # Первый урок бесплатный
                        )
                        session.add(lesson)
                        generated_lessons += 1

                        logger.info(f"Generated lesson {generated_lessons}/{total_lessons}: {lesson_title}")

                # Сохраняем всё в БД
                await session.commit()

                logger.info(f"Course generation completed: {course_slug}. Total lessons: {generated_lessons}")
                return True

        except Exception as e:
            logger.error(f"Failed to generate course {course_slug}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# Глобальный экземпляр сервиса
_course_generator: Optional[CourseGeneratorService] = None


def get_course_generator() -> CourseGeneratorService:
    """
    Возвращает глобальный экземпляр CourseGeneratorService.

    Returns:
        CourseGeneratorService: Сервис для генерации курсов
    """
    global _course_generator
    if _course_generator is None:
        _course_generator = CourseGeneratorService()
    return _course_generator
