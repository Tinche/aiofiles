SRC_DIR := src
TESTS_DIR := tests
TARGET_DIRS := $(SRC_DIR) $(TESTS_DIR)

.PHONY: format lint test

format:
	pdm run black $(TARGET_DIRS)

test:
	pdm run pytest -x --ff $(TESTS_DIR)

lint:
	pdm run flake8 $(TARGET_DIRS) && pdm run black --check $(TARGET_DIRS)
