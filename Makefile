py_dirs := l1nkzip
py_files = $(wildcard l1nkzip/*.py)

env_ok:
	python3 -m venv venv
	venv/bin/pip install -U pip
	venv/bin/pip install -r requirements.txt
	touch env_ok

.PHONY: fmt
fmt: env_ok
	venv/bin/isort --sp .isort.cfg $(py_dirs)
	venv/bin/black $(py_files)

.PHONY: check
check: env_ok
	venv/bin/python -m mypy \
		--check-untyped-defs \
		--ignore-missing-imports \
		$(py_dirs)
	venv/bin/python -m flake8 --select F $(py_dirs)
	venv/bin/isort --sp .isort.cfg $(py_files) --check
	venv/bin/black --check $(py_files)

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
