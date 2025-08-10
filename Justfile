src_dir := "src"
tests_dir := "tests"
code_dirs := src_dir + " " + tests_dir

# list available rules
default:
    just --list

# build the project
build:
	uv build

# install dependencies
sync:
	uv sync --group lint --group test --group tox

# check the code
check:
	ruff format --check {{ code_dirs }}
	ruff check {{ code_dirs }}
	mypy {{ src_dir }}  # lint only the source code

# run coverage
coverage:
	coverage run -m pytest {{ tests_dir }}

# lint the code (including formatting)
lint *files=".":
	ruff format {{ files }}
	ruff check --fix {{ files }}

# run the tests
test *args:
	pytest {{ args }}
