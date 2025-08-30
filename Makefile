py_dirs := l1nkzip
py_files = $(wildcard l1nkzip/*.py)

.PHONY: fmt
fmt:
	uv run -- ruff check --fix $(py_dirs)
	uv run -- ruff format $(py_dirs)

.PHONY: check
check:
	uv run -- python -m mypy \
		--check-untyped-defs \
		--ignore-missing-imports \
		$(py_dirs)
	uv run -- ruff check $(py_dirs)
	uv run -- ruff format --check $(py_dirs)

.PHONY: test
test: check
	uv run -- python -m pytest tests/ -v

.PHONY: run_dev
run_dev:
	uv run -- uvicorn l1nkzip.main:app --reload

build: test
	docker build -t l1nkzip .

push/%: build
	docker tag l1nkzip:latest dorogoy/l1nkzip:$(notdir $@)
	docker tag l1nkzip:latest dorogoy/l1nkzip:latest
	docker push dorogoy/l1nkzip:$(notdir $@)
	docker push dorogoy/l1nkzip:latest

