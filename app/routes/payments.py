"""
Роуты для обработки платежей через ЮKassa.
Создание платежей, обработка webhook, страницы успеха/ошибки.
"""
from quart import Blueprint, request, jsonify, render_template, redirect, url_for
from quart_auth import login_required, current_user
from loguru import logger

from app.services.yookassa import get_yookassa_service
from app.data.courses import COURSES

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments/create", methods=["POST"])
@login_required
async def create_payment():
    """
    Создает новый платеж для покупки курса.

    Ожидает JSON:
    {
        "course_id": "chatgpt-basics",
        "return_url": "https://neuro-magic.ru/payment/success" (опционально)
    }

    Возвращает:
    {
        "success": true,
        "payment_id": 123,
        "confirmation_url": "https://yoomoney.ru/checkout/...",
        "amount": 1990.00,
        "course_title": "ChatGPT для начинающих"
    }
    """
    try:
        data = await request.get_json()
        course_id = data.get("course_id")
        return_url = data.get("return_url")

        if not course_id:
            return jsonify({"success": False, "error": "course_id is required"}), 400

        # Находим курс
        course = COURSES.get(course_id)
        if not course:
            return jsonify({"success": False, "error": "Course not found"}), 404

        # Получаем цену курса (пока захардкодим, потом добавим в модель курса)
        # TODO: Добавить поле price в модель Course
        course_prices = {
            "chatgpt-basics": 1990,
            "prompt-engineering": 2490,
            "midjourney-master": 3490,
            "stable-diffusion": 3990,
            "ai-agents": 4990,
            "fine-tuning": 5990,
            "rag-systems": 6990,
            "langchain-dev": 7990,
        }

        amount = course_prices.get(course_id, 1990)  # По умолчанию 1990 руб
        description = f"Покупка курса: {course['title']}"

        # Создаем платеж через сервис ЮKassa
        yookassa_service = get_yookassa_service()
        payment = await yookassa_service.create_payment(
            user_id=current_user.auth_id,
            course_id=course_id,
            amount=amount,
            description=description,
            return_url=return_url
        )

        if not payment:
            logger.error(f"Failed to create payment for user {current_user.auth_id}, course {course_id}")
            return jsonify({
                "success": False,
                "error": "Failed to create payment. Please try again later."
            }), 500

        logger.info(
            f"Payment created successfully: #{payment.id} for user {current_user.auth_id}, "
            f"course {course_id}, amount {amount} RUB"
        )

        return jsonify({
            "success": True,
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation_url,
            "amount": float(payment.amount),
            "course_title": course["title"]
        }), 200

    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@payments_bp.route("/payment/success", methods=["GET"])
async def payment_success():
    """
    Страница успешной оплаты.
    Пользователь попадает сюда после завершения оплаты на стороне ЮKassa.
    """
    return await render_template("payments/success.html")


@payments_bp.route("/payment/cancel", methods=["GET"])
async def payment_cancel():
    """
    Страница отмены оплаты.
    Пользователь попадает сюда если отменил оплату.
    """
    return await render_template("payments/cancel.html")


@payments_bp.route("/payments/webhook", methods=["POST"])
async def payment_webhook():
    """
    Обрабатывает webhook уведомления от ЮKassa.

    ЮKassa отправляет уведомления о событиях платежа:
    - payment.succeeded - платеж успешно завершен
    - payment.waiting_for_capture - ожидает подтверждения
    - payment.canceled - платеж отменен

    ВАЖНО: Webhook URL должен быть настроен в личном кабинете ЮKassa.
    ВАЖНО: Webhook работает только по HTTPS.
    """
    try:
        webhook_data = await request.get_json()

        logger.info(f"Received webhook from YooKassa: {webhook_data}")

        # Обрабатываем webhook через сервис
        yookassa_service = get_yookassa_service()
        success = await yookassa_service.process_webhook(webhook_data)

        if success:
            # Возвращаем HTTP 200 чтобы ЮKassa знала что уведомление обработано
            return jsonify({"status": "ok"}), 200
        else:
            logger.error("Failed to process webhook")
            return jsonify({"status": "error"}), 400

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        # Всё равно возвращаем 200 чтобы ЮKassa не продолжала повторные попытки
        return jsonify({"status": "error"}), 200
