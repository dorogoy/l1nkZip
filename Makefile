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
	${MAKE} test-unit
	${MAKE} test-api
	${MAKE} test-integration

.PHONY: test-unit
test-unit: check
	uv run -- python -m pytest tests/unit/ -v

.PHONY: test-api
test-api: check
	uv run -- python -m pytest tests/api/ -v

.PHONY: test-integration
test-integration: check
	uv run -- python -m pytest tests/integration/ -v

.PHONY: test-cov
test-cov: check
	uv run -- coverage erase
	uv run -- python -m pytest tests/unit/ --cov=l1nkzip --cov-append --no-cov-on-fail -v
	uv run -- python -m pytest tests/api/ --cov=l1nkzip --cov-append --no-cov-on-fail -v
	uv run -- python -m pytest tests/integration/ --cov=l1nkzip --cov-append --no-cov-on-fail -v
	uv run -- coverage html
	uv run -- coverage report --show-missing

.PHONY: test-cov-xml
test-cov-xml: check
	uv run -- coverage erase
	uv run -- python -m pytest tests/unit/ --cov=l1nkzip --cov-append --no-cov-on-fail -v
	uv run -- python -m pytest tests/api/ --cov=l1nkzip --cov-append --no-cov-on-fail -v
	uv run -- python -m pytest tests/integration/ --cov=l1nkzip --cov-append --no-cov-on-fail -v
	uv run -- coverage xml
	uv run -- coverage report --show-missing

.PHONY: coverage-html
coverage-html: test-cov
	@echo "Coverage report generated in htmlcov/index.html"
	@echo "Open htmlcov/index.html in your browser to view the report"

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

