"""
Роуты для работы с курсами (детальные страницы, покупка, личный кабинет)
"""
from quart import Blueprint, render_template, abort, session, redirect, url_for, request
from quart_auth import login_required, current_user

from app.services.courses import get_course_by_slug
from app.data.courses import get_course_full_data
from app.models.user_course import UserCourse
from app.database import engine
from sqlalchemy import text

bp = Blueprint("courses", __name__, url_prefix="/courses")


@bp.route("/<slug>")
async def course_detail(slug: str):
    """
    Детальная страница курса с полной информацией и программой
    """
    # Получаем базовые данные курса
    course = get_course_by_slug(slug)
    if not course:
        abort(404)
    
    # Получаем расширенные данные (цена, программа)
    course_data = get_course_full_data(slug)
    if not course_data:
        abort(404)
    
    # Проверяем, куплен ли курс пользователем
    is_purchased = False
    if session.get('user_id'):
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT id FROM user_courses WHERE user_id = :user_id AND course_slug = :slug"),
                {"user_id": session['user_id'], "slug": slug}
            )
            is_purchased = result.fetchone() is not None
    
    return await render_template(
        "courses/detail.html",
        course=course,
        course_data=course_data,
        is_purchased=is_purchased,
        page_title=f"{course.title} | Нейромагия"
    )


@bp.route("/<slug>/buy")
@login_required
async def buy_course(slug: str):
    """
    Страница покупки курса (пока mock)
    """
    # Получаем данные курса
    course = get_course_by_slug(slug)
    if not course:
        abort(404)
    
    course_data = get_course_full_data(slug)
    if not course_data:
        abort(404)
    
    # Проверяем, не куплен ли уже
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id FROM user_courses WHERE user_id = :user_id AND course_slug = :slug"),
            {"user_id": session['user_id'], "slug": slug}
        )
        if result.fetchone():
            # Уже куплен - редирект на страницу курса
            return redirect(url_for('courses.my_course', slug=slug))
    
    return await render_template(
        "courses/buy.html",
        course=course,
        price=course_data['price'],
        page_title=f"Оплата курса: {course.title}"
    )


@bp.route("/<slug>/buy/confirm", methods=['POST'])
@login_required
async def confirm_purchase(slug: str):
    """
    Подтверждение покупки (mock оплата)
    """
    course = get_course_by_slug(slug)
    if not course:
        abort(404)
    
    course_data = get_course_full_data(slug)
    if not course_data:
        abort(404)
    
    # Создаём запись о покупке
    async with engine.begin() as conn:
        # Проверяем, не куплен ли уже
        result = await conn.execute(
            text("SELECT id FROM user_courses WHERE user_id = :user_id AND course_slug = :slug"),
            {"user_id": session['user_id'], "slug": slug}
        )
        if not result.fetchone():
            # Добавляем покупку
            await conn.execute(
                text("""INSERT INTO user_courses (user_id, course_slug, price_paid, payment_method, status)
                   VALUES (:user_id, :slug, :price, :method, :status)"""),
                {"user_id": session['user_id'], "slug": slug, "price": course_data['price'], "method": 'mock', "status": 'paid'}
            )
    
    # Редирект на страницу "Мои курсы"
    return redirect(url_for('courses.my_courses'))


@bp.route("/my")
@login_required
async def my_courses():
    """
    Страница "Мои курсы" - личный кабинет с купленными курсами
    """
    user_id = session.get('user_id')
    
    # Получаем все купленные курсы пользователя
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""SELECT course_slug, purchased_at, price_paid, status
               FROM user_courses
               WHERE user_id = :user_id
               ORDER BY purchased_at DESC"""),
            {"user_id": user_id}
        )
        purchases = result.fetchall()
    
    # Формируем список курсов с полными данными
    my_courses_list = []
    for purchase in purchases:
        course = get_course_by_slug(purchase[0])
        if course:
            course_data = get_course_full_data(purchase[0])
            my_courses_list.append({
                'course': course,
                'purchased_at': purchase[1],
                'price_paid': purchase[2],
                'status': purchase[3],
                'duration_weeks': course_data.get('duration_weeks', 4)
            })
    
    return await render_template(
        "courses/my_courses.html",
        courses=my_courses_list,
        page_title="Мои курсы | Нейромагия"
    )


@bp.route("/my/<slug>")
@login_required
async def my_course(slug: str):
    """
    Страница конкретного купленного курса (пока заглушка)
    """
    user_id = session.get('user_id')
    
    # Проверяем доступ к курсу
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, status FROM user_courses WHERE user_id = :user_id AND course_slug = :slug"),
            {"user_id": user_id, "slug": slug}
        )
        purchase = result.fetchone()
        
        if not purchase:
            abort(403)  # Нет доступа
    
    course = get_course_by_slug(slug)
    if not course:
        abort(404)
    
    course_data = get_course_full_data(slug)
    
    return await render_template(
        "courses/learn.html",
        course=course,
        course_data=course_data,
        page_title=f"Обучение: {course.title}"
    )

