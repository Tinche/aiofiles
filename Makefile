TEST_DIR := tests
DIRS := src $(TEST_DIR)

.PHONY: test lint

check:
	pdm run ruff format --check $(DIRS)
	pdm run ruff check $(DIRS)

format:
	pdm run ruff format $(DIRS)

lint: format
	pdm run ruff check --fix $(DIRS)

test:
	pdm run pytest -x --ff $(TEST_DIR)