"""
Роуты для обработки платежей.
"""
from quart import Blueprint, request, jsonify, render_template
from quart_auth import login_required, current_user
from loguru import logger

from app.data.courses import COURSES

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments/create", methods=["POST"])
@login_required
async def create_payment():
    """
    Создает новый платеж для покупки курса.
    """
    return jsonify({
        "success": False,
        "error": "Payment system is currently unavailable"
    }), 503


@payments_bp.route("/payment/success", methods=["GET"])
async def payment_success():
    """
    Страница успешной оплаты.
    """
    return await render_template("payments/success.html")


@payments_bp.route("/payment/cancel", methods=["GET"])
async def payment_cancel():
    """
    Страница отмены оплаты.
    """
    return await render_template("payments/cancel.html")


@payments_bp.route("/payments/webhook", methods=["POST"])
async def payment_webhook():
    """
    Обрабатывает webhook уведомления.
    """
    return jsonify({"status": "ignored"}), 200
