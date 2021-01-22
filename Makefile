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
