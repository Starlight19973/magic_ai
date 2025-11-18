"""
Роуты для магического квеста (бесплатное погружение)
"""

from quart import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from app.data.quest_v2 import get_question, get_first_question, calculate_recommendation
import httpx
import os

bp = Blueprint("quest", __name__)


@bp.route("/free-quest")
async def quest_start():
    """
    Стартовая страница квеста
    Очищаем предыдущую сессию и начинаем новый квест
    """
    # Очищаем старые данные квеста
    session.pop('quest_answers', None)
    session.pop('quest_current', None)
    
    # Инициализируем новый квест
    session['quest_answers'] = []
    session['quest_current'] = 'q1'
    
    first_question = get_first_question()
    
    return await render_template(
        "quest/question.html",
        question=first_question,
        progress=10,  # 1 из 10 вопросов
        page_title="Магический квест | Нейромагия"
    )


@bp.route("/free-quest/question/<question_id>")
async def quest_question(question_id: str):
    """
    Отображение конкретного вопроса
    """
    question = get_question(question_id)
    
    if not question:
        # Если вопрос не найден, редирект на старт
        return redirect(url_for('quest.quest_start'))
    
    # Обновляем текущий вопрос в сессии
    session['quest_current'] = question_id
    
    # Вычисляем прогресс (примерно)
    answers = session.get('quest_answers', [])
    progress = min(10 + len(answers) * 9, 100)  # От 10% до 100%
    
    return await render_template(
        "quest/question.html",
        question=question,
        progress=progress,
        page_title="Магический квест | Нейромагия"
    )


@bp.route("/free-quest/answer", methods=["POST"])
async def quest_answer():
    """
    Обработка ответа пользователя
    """
    data = await request.form
    
    current_question_id = session.get('quest_current')
    answer_id = data.get('answer_id')
    answer_text = data.get('answer_text', '')  # Для текстовых ответов
    
    if not current_question_id:
        return redirect(url_for('quest.quest_start'))
    
    current_question = get_question(current_question_id)
    
    if not current_question:
        return redirect(url_for('quest.quest_start'))
    
    # Сохраняем ответ в сессию
    answers = session.get('quest_answers', [])
    
    # Находим выбранный ответ и извлекаем метаданные
    answer_data = {
        'question_id': current_question_id,
        'answer_id': answer_id,
        'answer_text': answer_text
    }
    
    next_question_id = None  # Инициализация переменной
    
    # Если это choice вопрос, извлекаем метаданные
    if current_question['type'] == 'choice' and answer_id:
        for ans in current_question['answers']:
            if ans['id'] == answer_id:
                # Копируем все метаданные кроме текста и next
                for key, value in ans.items():
                    if key not in ['id', 'text', 'next']:
                        answer_data[key] = value
                
                # Определяем следующий вопрос
                next_question_id = ans.get('next')
                break
    elif current_question['type'] == 'text':
        # Для текстового вопроса
        next_question_id = current_question.get('next')
        answer_data['user_prompt'] = answer_text
    
    answers.append(answer_data)
    session['quest_answers'] = answers
    
    # Переход к следующему вопросу или результатам
    if not next_question_id:
        return redirect(url_for('quest.quest_start'))
    
    if next_question_id == 'results':
        return redirect(url_for('quest.quest_results'))
    elif next_question_id == 'challenge':
        return redirect(url_for('quest.quest_challenge'))
    elif next_question_id == 'contact':
        return redirect(url_for('quest.quest_contact'))
    else:
        return redirect(url_for('quest.quest_question', question_id=next_question_id))


@bp.route("/free-quest/challenge")
async def quest_challenge():
    """
    Финальная задачка квеста
    """
    challenge = get_question('challenge')
    
    if not challenge:
        return redirect(url_for('quest.quest_start'))
    
    answers = session.get('quest_answers', [])
    progress = 90  # Почти финал
    
    return await render_template(
        "quest/challenge.html",
        challenge=challenge,
        progress=progress,
        page_title="Финальное испытание | Нейромагия"
    )


@bp.route("/free-quest/contact")
async def quest_contact():
    """
    Форма для сбора контактов
    """
    contact = get_question('contact')
    
    if not contact:
        return redirect(url_for('quest.quest_start'))
    
    answers = session.get('quest_answers', [])
    progress = 95  # Почти финал
    
    return await render_template(
        "quest/contact.html",
        contact=contact,
        progress=progress,
        page_title="Оставьте контакты | Нейромагия"
    )


@bp.route("/free-quest/contact", methods=["POST"])
async def quest_contact_submit():
    """
    Обработка контактной формы и отправка в Telegram
    """
    form_data = await request.form
    
    telegram = form_data.get('telegram', '').strip()
    phone = form_data.get('phone', '').strip()
    name = form_data.get('name', '').strip()
    
    # Проверяем, что хотя бы один контакт указан
    if not telegram and not phone:
        return await render_template(
            "quest/contact.html",
            contact=get_question('contact'),
            error="Пожалуйста, укажите хотя бы один способ связи",
            progress=95,
            page_title="Оставьте контакты | Нейромагия"
        )
    
    # Сохраняем контакты в сессию
    session['quest_contact'] = {
        'telegram': telegram,
        'phone': phone,
        'name': name
    }
    
    # Отправляем в Telegram бот
    await send_to_telegram_bot(session)
    
    # Редирект на результаты
    return redirect(url_for('quest.quest_results'))


async def send_to_telegram_bot(session_data):
    """
    Отправка заявки в Telegram бот
    """
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')  # ID чата куда слать заявки
    
    if not bot_token or not chat_id:
        current_app.logger.warning("Telegram bot credentials not configured")
        return
    
    # Формируем данные из квеста
    answers = session_data.get('quest_answers', [])
    contact = session_data.get('quest_contact', {})
    recommendation = session_data.get('quest_recommendation', {})
    
    # Извлекаем проект мечты
    user_project = ""
    for answer in answers:
        if answer.get('user_prompt'):
            user_project = answer['user_prompt']
    
    # Извлекаем назначение и доступ
    purpose = ""
    access = ""
    for answer in answers:
        if 'purpose' in answer:
            purpose = answer['purpose']
        if 'access' in answer:
            access = answer['access']
    
    # Рекомендованные курсы
    courses = []
    if recommendation.get('recommendations'):
        courses = [rec['title'] for rec in recommendation['recommendations'][:3]]
    
    # Формируем сообщение
    message = f"""
🎓 **НОВАЯ ЗАЯВКА С КВЕСТА**

👤 **Контакты:**
Имя: {contact.get('name', 'Не указано')}
Telegram: {contact.get('telegram', 'Не указано')}
Телефон: {contact.get('phone', 'Не указан')}

🎯 **Цель использования AI:**
{purpose or 'Не определена'}

🌐 **Доступ к нейросетям:**
{access or 'Не определён'}

💡 **Проект мечты:**
{user_project or 'Не указан'}

📚 **Рекомендованные курсы:**
{chr(10).join(f"• {course}" for course in courses) if courses else 'Не определены'}

---
Время: {import_datetime()}
"""
    
    # Отправляем в Telegram
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            await client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            })
            current_app.logger.info(f"Quest application sent to Telegram: {contact.get('telegram', contact.get('phone'))}")
    except Exception as e:
        current_app.logger.error(f"Failed to send to Telegram: {e}")


def import_datetime():
    """Вспомогательная функция для получения текущего времени"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@bp.route("/free-quest/results")
async def quest_results():
    """
    Результаты квеста с рекомендациями
    """
    answers = session.get('quest_answers', [])
    
    if not answers:
        return redirect(url_for('quest.quest_start'))
    
    # Вычисляем рекомендации на основе ответов
    recommendation = calculate_recommendation(answers)
    
    # Сохраняем рекомендации в сессию для дальнейшего использования
    session['quest_recommendation'] = recommendation
    
    return await render_template(
        "quest/results.html",
        recommendation=recommendation,
        progress=100,
        page_title="Ваш путь в Нейромагии"
    )


@bp.route("/free-quest/restart")
async def quest_restart():
    """
    Перезапуск квеста
    """
    session.pop('quest_answers', None)
    session.pop('quest_current', None)
    session.pop('quest_recommendation', None)
    
    return redirect(url_for('quest.quest_start'))

