from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Author(BaseModel):
    name: str
    title: str
    avatar: str


class Course(BaseModel):
    slug: str
    title: str
    tagline: str
    description: str
    price: int
    duration_weeks: int
    level: Literal["beginner", "junior", "middle", "senior"]
    format: Literal["live", "recorded", "hybrid"]
    technologies: list[str]
    badges: list[str]
    cover: str
    highlight: str
    author: Author


class Review(BaseModel):
    author: str
    role: str
    quote: str
    avatar: str

