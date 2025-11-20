"""
Сервис для работы с ЮKassa API.
Создание платежей, получение информации, обработка webhooks.
"""
import uuid
from datetime import datetime
from typing import Dict, Optional, Any

from loguru import logger
from yookassa import Configuration, Payment as YooKassaPayment

from app.config import Settings
from app.models import Payment
from app.database import get_session


class YooKassaService:
    """
    Сервис для работы с платежной системой ЮKassa.

    Основные методы:
    - create_payment() - создание платежа
    - get_payment_info() - получение информации о платеже
    - process_webhook() - обработка webhook уведомления
    """

    def __init__(self, settings: Settings):
        """
        Инициализация сервиса ЮKassa.

        Args:
            settings: Настройки приложения с учетными данными ЮKassa
        """
        self.settings = settings

        # Инициализируем ЮKassa SDK
        if settings.yookassa_shop_id and settings.yookassa_secret_key:
            Configuration.account_id = settings.yookassa_shop_id
            Configuration.secret_key = settings.yookassa_secret_key
            logger.info("YooKassa SDK initialized successfully")
        else:
            logger.warning("YooKassa credentials not found in settings")

    async def create_payment(
        self,
        user_id: int,
        course_id: str,
        amount: float,
        description: str,
        return_url: Optional[str] = None
    ) -> Optional[Payment]:
        """
        Создает новый платеж в системе ЮKassa.

        Args:
            user_id: ID пользователя
            course_id: ID курса
            amount: Сумма платежа в рублях
            description: Описание платежа
            return_url: URL для возврата после оплаты (опционально)

        Returns:
            Payment: Созданный объект платежа или None в случае ошибки
        """
        try:
            # Генерируем уникальный ключ идемпотентности
            idempotence_key = str(uuid.uuid4())

            # URL для возврата после оплаты
            if not return_url:
                return_url = self.settings.yookassa_return_url

            # Создаем платеж через API ЮKassa
            yookassa_payment = YooKassaPayment.create({
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url
                },
                "capture": True,  # Автоматическое списание средств
                "description": description,
                "metadata": {
                    "user_id": str(user_id),
                    "course_id": course_id
                }
            }, idempotence_key)

            # Сохраняем платеж в нашей БД
            async with get_session() as session:
                payment = Payment(
                    user_id=user_id,
                    course_id=course_id,
                    yookassa_payment_id=yookassa_payment.id,
                    amount=amount,
                    currency="RUB",
                    status=yookassa_payment.status,
                    description=description,
                    confirmation_url=yookassa_payment.confirmation.confirmation_url
                )
                session.add(payment)
                await session.commit()
                await session.refresh(payment)

                logger.info(
                    f"Payment created: #{payment.id} for user {user_id}, "
                    f"course {course_id}, amount {amount} RUB"
                )

                return payment

        except Exception as e:
            logger.error(f"Failed to create payment: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def get_payment_info(self, yookassa_payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о платеже из ЮKassa.

        Args:
            yookassa_payment_id: ID платежа в системе ЮKassa

        Returns:
            Dict: Информация о платеже или None в случае ошибки
        """
        try:
            yookassa_payment = YooKassaPayment.find_one(yookassa_payment_id)

            return {
                "id": yookassa_payment.id,
                "status": yookassa_payment.status,
                "amount": float(yookassa_payment.amount.value),
                "currency": yookassa_payment.amount.currency,
                "description": yookassa_payment.description,
                "created_at": yookassa_payment.created_at,
                "paid": yookassa_payment.paid,
                "metadata": yookassa_payment.metadata
            }

        except Exception as e:
            logger.error(f"Failed to get payment info: {str(e)}")
            return None

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает webhook уведомление от ЮKassa.

        Возможные события:
        - payment.succeeded - платеж успешно завершен
        - payment.waiting_for_capture - ожидает подтверждения
        - payment.canceled - платеж отменен

        Args:
            webhook_data: Данные webhook от ЮKassa

        Returns:
            bool: True если обработано успешно, False в случае ошибки
        """
        try:
            event = webhook_data.get("event")
            payment_object = webhook_data.get("object")

            if not event or not payment_object:
                logger.error("Invalid webhook data: missing event or object")
                return False

            yookassa_payment_id = payment_object.get("id")
            status = payment_object.get("status")

            logger.info(f"Processing webhook: event={event}, payment={yookassa_payment_id}, status={status}")

            # Находим платеж в нашей БД
            async with get_session() as session:
                from sqlalchemy import select

                stmt = select(Payment).where(Payment.yookassa_payment_id == yookassa_payment_id)
                result = await session.execute(stmt)
                payment = result.scalar_one_or_none()

                if not payment:
                    logger.error(f"Payment not found in DB: {yookassa_payment_id}")
                    return False

                # Обновляем статус платежа
                payment.status = status
                payment.updated_at = datetime.utcnow()

                # Если платеж успешно завершен
                if event == "payment.succeeded":
                    payment.paid_at = datetime.utcnow()

                    logger.info(f"Payment succeeded: #{payment.id}, user={payment.user_id}, course={payment.course_id}")

                    # Отправляем email пользователю о покупке
                    try:
                        from app.models import User
                        from app.services.email import send_purchase_email
                        from app.data.courses import COURSES

                        # Получаем данные пользователя
                        user_stmt = select(User).where(User.id == payment.user_id)
                        user_result = await session.execute(user_stmt)
                        user = user_result.scalar_one_or_none()

                        if user:
                            # Получаем данные курса
                            course = COURSES.get(payment.course_id)
                            course_title = course["title"] if course else payment.description

                            # Отправляем email
                            await send_purchase_email(
                                email=user.email,
                                username=user.username,
                                course_title=course_title,
                                course_id=payment.course_id,
                                amount=float(payment.amount)
                            )
                            logger.info(f"Purchase email sent to {user.email}")

                            # TODO: Активировать доступ к курсу (обновить UserCourse)
                        else:
                            logger.error(f"User not found: {payment.user_id}")

                    except Exception as e:
                        logger.error(f"Failed to send purchase email: {str(e)}")
                        # Не прерываем обработку webhook из-за ошибки email

                await session.commit()

                logger.info(f"Webhook processed successfully for payment #{payment.id}")
                return True

        except Exception as e:
            logger.error(f"Failed to process webhook: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def verify_webhook_signature(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Проверяет подлинность webhook уведомления.

        Для дополнительной безопасности можно проверить:
        1. IP адрес отправителя (должен быть из диапазона ЮKassa)
        2. Статус платежа через API (сверить с уведомлением)

        Args:
            webhook_data: Данные webhook

        Returns:
            bool: True если подлинность подтверждена
        """
        # TODO: Реализовать проверку IP адреса
        # Разрешенные диапазоны ЮKassa:
        # 185.71.76.0/27, 185.71.77.0/27, 77.75.153.0/25, 77.75.156.11,
        # 77.75.156.35, 77.75.154.128/25, 2a02:5180::/32

        # Пока возвращаем True
        # В production нужно добавить проверку
        return True


# Глобальный экземпляр сервиса
_yookassa_service: Optional[YooKassaService] = None


def get_yookassa_service() -> YooKassaService:
    """
    Возвращает глобальный экземпляр YooKassaService.

    Returns:
        YooKassaService: Сервис для работы с ЮKassa
    """
    global _yookassa_service
    if _yookassa_service is None:
        settings = Settings()
        _yookassa_service = YooKassaService(settings)
    return _yookassa_service
