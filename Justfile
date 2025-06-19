tests_dir := "tests"
code_dirs := "src" + " " + tests_dir
run_prefix := if env_var_or_default("VIRTUAL_ENV", "") == "" { "uv run " } else { "" }

check:
	{{ run_prefix }}ruff format --check {{ code_dirs }}
	{{ run_prefix }}ruff check {{ code_dirs }}

coverage:
	{{ run_prefix }}coverage run -m pytest {{ tests_dir }}

format:
	{{ run_prefix }}ruff format {{ code_dirs }}

lint: format
	{{ run_prefix }}ruff check --fix {{ code_dirs }}

test:
	{{ run_prefix }}pytest -x --ff {{ tests_dir }}