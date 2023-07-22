env_ok:
	python3 -m venv env
	env/bin/pip install --upgrade -r requirements.txt
	touch env_ok

.PHONY: run
run: env_ok
	env/bin/mkdocs serve

.PHONY: deploy
deploy: env_ok
	env/bin/mkdocs gh-deploy

.PHONY: clean
clean:
	rm -rf env env_ok site
