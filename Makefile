.PHONY: install dev lint test

install:
	python -m pip install -r requirements.txt

dev:
	quart --app main:app --debug run

lint:
	ruff check app

test:
	pytest

