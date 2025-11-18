from __future__ import annotations

from quart import Blueprint, abort, render_template

from app.services.courses import (
    get_catalog,
    get_course_by_slug,
    get_featured_courses,
    get_reviews,
)

bp = Blueprint("public", __name__)


@bp.get("/")
async def index():
    featured = get_featured_courses()
    catalog = get_catalog()
    reviews = list(get_reviews())
    payload = {
        "featured": [course.model_dump() for course in featured],
        "catalog": [course.model_dump() for course in catalog],
        "reviews": [review.model_dump() for review in reviews],
    }
    return await render_template(
        "index.html",
        featured=featured,
        catalog=catalog,
        reviews=reviews,
        payload=payload,
        page_title="Нейромагия — курсы по ИИ",
    )


@bp.get("/courses")
async def courses():
    catalog = get_catalog()
    payload = {"catalog": [course.model_dump() for course in catalog]}
    return await render_template("course.html", catalog=catalog, payload=payload, page_title="Каталог курсов")


@bp.get("/courses/<string:slug>")
async def course_details(slug: str):
    course = get_course_by_slug(slug)
    if not course:
        abort(404)
    payload = {"catalog": [course.model_dump()]}
    return await render_template(
        "course.html",
        catalog=[course],
        payload=payload,
        page_title=course.title,
    )


@bp.get("/about")
async def about():
    return await render_template(
        "about.html",
        page_title="О нас — Нейромагия",
    )
