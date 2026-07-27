default:
    @just --list

gate:
    uv run ruff check .
    uv run ruff format --check .
    uv run ty check
    uv run pytest -q

test *ARGS:
    uv run pytest -q {{ARGS}}

lint:
    uv run ruff check . && uv run ruff format --check .
