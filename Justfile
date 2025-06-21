src_dir := "src"
tests_dir := "tests"
code_dirs := src_dir + " " + tests_dir

check:
	ruff format --check {{ code_dirs }}
	ruff check {{ code_dirs }}

coverage:
	coverage run -m pytest {{ tests_dir }}

format:
	ruff format {{ code_dirs }}

lint: format
	ruff check --fix {{ code_dirs }}

test:
	pytest {{ tests_dir }}
