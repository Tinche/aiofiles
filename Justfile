src_dir := "src"
tests_dir := "tests"
code_dirs := src_dir + " " + tests_dir

# https://just.systems/man/en/functions.html#environment-variables
run := if env("VIRTUAL_ENV", "") == "" { "uv run " } else { "" }

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
	{{ run }}ruff format --check {{ code_dirs }}
	{{ run }}ruff check {{ code_dirs }}
	{{ run }}mypy {{ src_dir }}  # lint only the source code

# run coverage
coverage:
	{{ run }}coverage run -m pytest {{ tests_dir }}

# lint the code (including formatting)
lint *files=".":
	{{ run }}ruff format {{ files }}
	{{ run }}ruff check --fix {{ files }}

# run the tests
test *args:
	{{ run }}pytest {{ args }}
