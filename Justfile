src_dir := "src"
tests_dir := "tests"
code_dirs := src_dir + " " + tests_dir

build:
	uv build

sync:
	uv sync --group lint --group test --group tox

check:
	ruff format --check {{ code_dirs }}
	ruff check {{ code_dirs }}
	mypy {{ src_dir }}  # lint only the source code

coverage:
	coverage run -m pytest {{ tests_dir }}

lint *files=".":
	ruff format {{ files }}
	ruff check --fix {{ files }}

test *args:
	pytest {{ args }}
