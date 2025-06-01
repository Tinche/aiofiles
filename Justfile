tests_dir := "tests"
code_dirs := "src" + " " + tests_dir

check:
	uv run ruff format --check {{ code_dirs }}
	uv run ruff check {{ code_dirs }}

coverage:
	uv run coverage run -m pytest {{ tests_dir }}

format:
	uv run ruff format {{ code_dirs }}

lint: format
	uv run ruff check --fix {{ code_dirs }}

test:
	uv run pytest -x --ff {{ tests_dir }}
