"""
Роуты для работы с курсами (детальные страницы, покупка, личный кабинет)
"""
from quart import Blueprint, render_template, abort, session, redirect, url_for, request, jsonify
from quart_auth import login_required, current_user
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.courses import get_course_by_slug
from app.data.courses import get_course_full_data
from app.models import UserCourse, CourseModule, Lesson, UserLessonProgress
from app.database import engine, AsyncSessionLocal
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
    Страница конкретного купленного курса с модулями и уроками
    """
    user_id = session.get('user_id')

    # Проверяем доступ к курсу
    async with AsyncSessionLocal() as db_session:
        result = await db_session.execute(
            select(UserCourse).where(
                UserCourse.user_id == user_id,
                UserCourse.course_slug == slug
            )
        )
        purchase = result.scalar_one_or_none()

        if not purchase:
            abort(403)  # Нет доступа

        # Получаем модули и уроки курса
        modules_result = await db_session.execute(
            select(CourseModule)
            .where(CourseModule.course_slug == slug)
            .order_by(CourseModule.order)
            .options(selectinload(CourseModule.lessons))
        )
        modules = list(modules_result.scalars().all())

        # Получаем прогресс пользователя по всем урокам
        progress_result = await db_session.execute(
            select(UserLessonProgress)
            .where(UserLessonProgress.user_id == user_id)
        )
        progress_map = {p.lesson_id: p for p in progress_result.scalars().all()}

        # Считаем общий прогресс
        total_lessons = sum(len(m.lessons) for m in modules)
        completed_lessons = sum(
            1 for m in modules
            for lesson in m.lessons
            if progress_map.get(lesson.id) and progress_map[lesson.id].status == "completed"
        )
        progress_percent = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0

    course = get_course_by_slug(slug)
    if not course:
        abort(404)

    course_data = get_course_full_data(slug)

    # Если есть модули, перенаправляем на первый урок первого модуля
    if modules and modules[0].lessons:
        first_lesson = modules[0].lessons[0]
        return redirect(url_for('courses.view_lesson', slug=slug, lesson_id=first_lesson.id))

    return await render_template(
        "courses/learn.html",
        course=course,
        course_data=course_data,
        modules=modules,
        progress_map=progress_map,
        progress_percent=progress_percent,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        page_title=f"Обучение: {course.title}"
    )


@bp.route("/my/<slug>/lesson/<int:lesson_id>")
@login_required
async def view_lesson(slug: str, lesson_id: int):
    """
    Просмотр конкретного урока
    """
    user_id = session.get('user_id')

    async with AsyncSessionLocal() as db_session:
        # Проверяем доступ к курсу
        purchase_result = await db_session.execute(
            select(UserCourse).where(
                UserCourse.user_id == user_id,
                UserCourse.course_slug == slug
            )
        )
        if not purchase_result.scalar_one_or_none():
            abort(403)

        # Получаем урок
        lesson_result = await db_session.execute(
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(selectinload(Lesson.module))
        )
        lesson = lesson_result.scalar_one_or_none()

        if not lesson or lesson.module.course_slug != slug:
            abort(404)

        # Получаем все модули и уроки для навигации
        modules_result = await db_session.execute(
            select(CourseModule)
            .where(CourseModule.course_slug == slug)
            .order_by(CourseModule.order)
            .options(selectinload(CourseModule.lessons))
        )
        modules = list(modules_result.scalars().all())

        # Получаем прогресс пользователя
        progress_result = await db_session.execute(
            select(UserLessonProgress)
            .where(UserLessonProgress.user_id == user_id)
        )
        progress_map = {p.lesson_id: p for p in progress_result.scalars().all()}

        # Считаем общий прогресс
        total_lessons = sum(len(m.lessons) for m in modules)
        completed_lessons = sum(
            1 for m in modules
            for l in m.lessons
            if progress_map.get(l.id) and progress_map[l.id].status == "completed"
        )
        progress_percent = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0

        # Получаем или создаём прогресс для текущего урока
        lesson_progress = progress_map.get(lesson_id)
        if not lesson_progress:
            lesson_progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status="in_progress",
                started_at=datetime.utcnow(),
                time_spent_seconds=0,
                quiz_attempts=0,
                quiz_passed=False
            )
            db_session.add(lesson_progress)
            await db_session.commit()
            await db_session.refresh(lesson_progress)
        elif lesson_progress.status == "not_started":
            lesson_progress.status = "in_progress"
            lesson_progress.started_at = datetime.utcnow()
            await db_session.commit()

        # Находим следующий урок
        next_lesson = None
        found_current = False
        for module in modules:
            for l in sorted(module.lessons, key=lambda x: x.order):
                if found_current:
                    next_lesson = l
                    break
                if l.id == lesson_id:
                    found_current = True
            if next_lesson:
                break

    course = get_course_by_slug(slug)
    course_data = get_course_full_data(slug)

    return await render_template(
        "courses/learn.html",
        course=course,
        course_data=course_data,
        modules=modules,
        current_lesson=lesson,
        lesson_progress=lesson_progress,
        next_lesson=next_lesson,
        progress_map=progress_map,
        progress_percent=progress_percent,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        page_title=f"{lesson.title} | {course.title}"
    )


@bp.route("/my/<slug>/lesson/<int:lesson_id>/complete", methods=['POST'])
@login_required
async def complete_lesson(slug: str, lesson_id: int):
    """
    Отметить урок как завершённый
    """
    user_id = session.get('user_id')

    async with AsyncSessionLocal() as db_session:
        # Проверяем доступ
        purchase_result = await db_session.execute(
            select(UserCourse).where(
                UserCourse.user_id == user_id,
                UserCourse.course_slug == slug
            )
        )
        if not purchase_result.scalar_one_or_none():
            abort(403)

        # Получаем прогресс
        progress_result = await db_session.execute(
            select(UserLessonProgress).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == lesson_id
            )
        )
        lesson_progress = progress_result.scalar_one_or_none()

        if lesson_progress:
            lesson_progress.status = "completed"
            lesson_progress.completed_at = datetime.utcnow()
            await db_session.commit()

    return jsonify({"success": True, "status": "completed"})


@bp.route("/my/<slug>/lesson/<int:lesson_id>/quiz", methods=['POST'])
@login_required
async def submit_quiz(slug: str, lesson_id: int):
    """
    Проверить ответы на квиз
    """
    user_id = session.get('user_id')
    data = await request.get_json()
    answers = data.get('answers', [])  # Список индексов выбранных ответов

    async with AsyncSessionLocal() as db_session:
        # Проверяем доступ
        purchase_result = await db_session.execute(
            select(UserCourse).where(
                UserCourse.user_id == user_id,
                UserCourse.course_slug == slug
            )
        )
        if not purchase_result.scalar_one_or_none():
            abort(403)

        # Получаем урок с квизом
        lesson_result = await db_session.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        lesson = lesson_result.scalar_one_or_none()

        if not lesson or not lesson.quiz_questions:
            abort(404)

        # Проверяем ответы
        questions = lesson.quiz_questions.get('questions', [])
        correct_count = 0
        results = []

        for idx, answer_idx in enumerate(answers):
            if idx < len(questions):
                question = questions[idx]
                is_correct = answer_idx == question.get('correct', -1)
                if is_correct:
                    correct_count += 1
                results.append({
                    'question_idx': idx,
                    'correct': is_correct,
                    'correct_answer': question.get('correct'),
                    'explanation': question.get('explanation', '')
                })

        # Вычисляем балл
        score = int((correct_count / len(questions) * 100)) if len(questions) > 0 else 0
        passed = score >= 70  # Порог прохождения 70%

        # Обновляем прогресс
        progress_result = await db_session.execute(
            select(UserLessonProgress).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == lesson_id
            )
        )
        lesson_progress = progress_result.scalar_one_or_none()

        if lesson_progress:
            lesson_progress.quiz_score = score
            lesson_progress.quiz_attempts += 1
            lesson_progress.quiz_passed = passed
            if passed and lesson_progress.status != "completed":
                lesson_progress.status = "completed"
                lesson_progress.completed_at = datetime.utcnow()
            await db_session.commit()

    return jsonify({
        "success": True,
        "score": score,
        "passed": passed,
        "correct_count": correct_count,
        "total_questions": len(questions),
        "results": results
    })

