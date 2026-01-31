TARGET ?= ""

format:
	isort ./app ./tests; black ./app ./tests

format-one:
	isort $(TARGET); black $(TARGET)

test:
	PYTHONPATH=. ENV=test pytest $(TARGET)

test-docker:
	docker compose -f docker-compose.test.yml up --abort-on-container-exit --build --exit-code-from auth-service

run:
	ENV=dev uvicorn app.main:app --log-level critical

migrate:
	ENV=dev alembic upgrade head