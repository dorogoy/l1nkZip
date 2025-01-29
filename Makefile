py_dirs := l1nkzip
py_files = $(wildcard l1nkzip/*.py)

env_ok:
	python3 -m venv venv
	venv/bin/pip install -U pip
	venv/bin/pip install -r requirements.txt
	touch env_ok

.PHONY: fmt
fmt: env_ok
	venv/bin/ruff check --fix $(py_dirs)
	venv/bin/ruff format $(py_dirs)

.PHONY: check
check: env_ok
	venv/bin/python -m mypy \
		--check-untyped-defs \
		--ignore-missing-imports \
		$(py_dirs)
	venv/bin/ruff check $(py_dirs)
	venv/bin/ruff format --check $(py_dirs)

.PHONY: test
test: check
	venv/bin/python -m unittest discover $(py_dirs) -p "*.py" -v

.PHONY: run_dev
run_dev: env_ok
	venv/bin/uvicorn l1nkzip.main:app --reload

build: test
	docker build -t l1nkzip .

push/%: build
	docker tag l1nkzip:latest dorogoy/l1nkzip:$(notdir $@)
	docker tag l1nkzip:latest dorogoy/l1nkzip:latest
	docker push dorogoy/l1nkzip:$(notdir $@)
	docker push dorogoy/l1nkzip:latest

clean:
	rm -rf venv/ env/ env_ok
