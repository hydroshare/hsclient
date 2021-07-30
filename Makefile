.DEFAULT_GOAL := all
isort = isort hsclient tests
black = black -S -l 120 --target-version py38 hsclient tests

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: docs
docs:
	mkdocs build

.PHONY: docs-serve
docs-serve:
	mkdocs serve

.PHONY: test
test:
	pytest -n 4 tests

.PHONY: test-cov
test-cov:
	pytest -n 4 --cov=hsclient --cov-report html
