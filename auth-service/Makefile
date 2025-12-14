TARGET ?= ""

format:
	isort ./app ./tests; black ./app	./tests

format_one:
	isort $(TARGET); black $(TARGET)

test:
	PYTHONPATH=. ENV=test pytest

test_one:
	PYTHONPATH=. ENV=test pytest -k $(TARGET)

run:
	ENV=dev uvicorn app.main:app --log-level critical
