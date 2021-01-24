
lint: pysonos
	flake8 pysonos
	pylint pysonos

test:
	py.test

docs:
	$(MAKE) -C doc html
	@echo "\033[95m\n\nBuild successful! View the docs at doc/_build/html/index.html.\n\033[0m"

clean:
	find . -name '*.py[co]' -delete

	find . -name '*~' -delete
	find . -name '__pycache__' -delete
	rm -rf pysonos.egg-info
	rm -rf dist
	$(MAKE) -C doc clean

.PHONY: lint docs test clean
