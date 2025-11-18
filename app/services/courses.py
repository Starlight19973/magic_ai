from __future__ import annotations

from typing import Iterable

from app.data.catalog import COURSES, REVIEWS
from app.schemas.course import Course, Review


def get_catalog() -> list[Course]:
    return COURSES


def get_featured_courses(limit: int = 3) -> list[Course]:
    return COURSES[:limit]


def get_course_by_slug(slug: str) -> Course | None:
    return next((course for course in COURSES if course.slug == slug), None)


def get_reviews() -> Iterable[Review]:
    return REVIEWS

