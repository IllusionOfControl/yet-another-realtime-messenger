TARGET ?= ""
VIRTUAL_ENVIRONMENT = auth-service

format:
	isort ./app ./tests; black ./app ./tests

format_one:
	isort $(TARGET); black $(TARGET)

test:
	PYTHONPATH=. ENV=test pytest $(TARGET)

run:
	ENV=dev uvicorn app.main:app --log-level error

migrate:
	ENV=dev alembic upgrade head