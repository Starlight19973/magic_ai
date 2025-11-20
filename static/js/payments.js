/**
 * Обработка покупки курсов через ЮKassa
 */

/**
 * Инициирует покупку курса
 * @param {string} courseId - ID курса
 * @param {string} courseTitle - Название курса
 * @param {number} price - Цена курса в рублях
 */
async function buyCourse(courseId, courseTitle, price) {
    try {
        // Показываем индикатор загрузки
        const button = event.target;
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Создание платежа...';

        // Отправляем запрос на создание платежа
        const response = await fetch('/payments/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                course_id: courseId,
                return_url: `${window.location.origin}/payment/success`
            })
        });

        const data = await response.json();

        if (data.success) {
            // Перенаправляем пользователя на страницу оплаты ЮKassa
            window.location.href = data.confirmation_url;
        } else {
            // Показываем ошибку
            alert(`Ошибка создания платежа: ${data.error || 'Неизвестная ошибка'}`);
            button.disabled = false;
            button.textContent = originalText;
        }
    } catch (error) {
        console.error('Error creating payment:', error);
        alert('Произошла ошибка при создании платежа. Попробуйте позже.');

        // Восстанавливаем кнопку
        const button = event.target;
        button.disabled = false;
        button.textContent = 'Купить курс';
    }
}

/**
 * Показывает модальное окно подтверждения покупки
 * @param {string} courseId - ID курса
 * @param {string} courseTitle - Название курса
 * @param {number} price - Цена курса в рублях
 */
function showPurchaseModal(courseId, courseTitle, price) {
    // Создаем модальное окно
    const modal = document.createElement('div');
    modal.id = 'purchase-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        backdrop-filter: blur(10px);
    `;

    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <h2 style="
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 20px;
                background: linear-gradient(135deg, #8b5cf6, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">
                Подтверждение покупки
            </h2>

            <p style="font-size: 16px; color: rgba(255, 255, 255, 0.7); margin: 0 0 10px;">
                Вы собираетесь приобрести курс:
            </p>

            <div style="
                background: rgba(139, 92, 246, 0.1);
                border: 2px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                padding: 20px;
                margin: 0 0 30px;
            ">
                <h3 style="
                    font-size: 20px;
                    font-weight: 600;
                    margin: 0 0 10px;
                    color: #8b5cf6;
                ">
                    ${courseTitle}
                </h3>
                <p style="
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0;
                    color: white;
                ">
                    ${price.toLocaleString('ru-RU')} ₽
                </p>
            </div>

            <div style="display: flex; gap: 15px;">
                <button
                    onclick="confirmPurchase('${courseId}', '${courseTitle}', ${price})"
                    style="
                        flex: 1;
                        padding: 15px;
                        font-size: 16px;
                        font-weight: 600;
                        border: none;
                        border-radius: 8px;
                        background: linear-gradient(135deg, #8b5cf6, #3b82f6);
                        color: white;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    "
                    onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 10px 30px rgba(139, 92, 246, 0.4)'"
                    onmouseout="this.style.transform=''; this.style.boxShadow=''"
                >
                    Перейти к оплате
                </button>
                <button
                    onclick="closePurchaseModal()"
                    style="
                        flex: 1;
                        padding: 15px;
                        font-size: 16px;
                        font-weight: 600;
                        border: 2px solid rgba(255, 255, 255, 0.2);
                        border-radius: 8px;
                        background: transparent;
                        color: rgba(255, 255, 255, 0.9);
                        cursor: pointer;
                        transition: all 0.3s ease;
                    "
                    onmouseover="this.style.background='rgba(255, 255, 255, 0.1)'; this.style.borderColor='rgba(255, 255, 255, 0.4)'"
                    onmouseout="this.style.background='transparent'; this.style.borderColor='rgba(255, 255, 255, 0.2)'"
                >
                    Отмена
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Закрываем при клике вне модального окна
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closePurchaseModal();
        }
    });
}

/**
 * Подтверждает покупку и создает платеж
 */
async function confirmPurchase(courseId, courseTitle, price) {
    closePurchaseModal();

    // Показываем индикатор загрузки
    showLoadingOverlay('Создаем платеж...');

    try {
        // Отправляем запрос на создание платежа
        const response = await fetch('/payments/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                course_id: courseId,
                return_url: `${window.location.origin}/payment/success`
            })
        });

        const data = await response.json();

        if (data.success) {
            // Перенаправляем пользователя на страницу оплаты ЮKassa
            window.location.href = data.confirmation_url;
        } else {
            hideLoadingOverlay();
            alert(`Ошибка создания платежа: ${data.error || 'Неизвестная ошибка'}`);
        }
    } catch (error) {
        console.error('Error creating payment:', error);
        hideLoadingOverlay();
        alert('Произошла ошибка при создании платежа. Попробуйте позже.');
    }
}

/**
 * Закрывает модальное окно покупки
 */
function closePurchaseModal() {
    const modal = document.getElementById('purchase-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Показывает overlay с загрузкой
 */
function showLoadingOverlay(message = 'Загрузка...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 20000;
        backdrop-filter: blur(10px);
    `;

    overlay.innerHTML = `
        <div style="
            width: 60px;
            height: 60px;
            border: 4px solid rgba(139, 92, 246, 0.3);
            border-top-color: #8b5cf6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <p style="
            margin-top: 20px;
            font-size: 18px;
            color: white;
            font-weight: 600;
        ">
            ${message}
        </p>
        <style>
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
    `;

    document.body.appendChild(overlay);
}

/**
 * Скрывает overlay с загрузкой
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}
