.PHONY: test lint

test:
	pdm run pytest -x --ff tests

lint:
	pdm run flake8 src tests && pdm run black --check src tests
