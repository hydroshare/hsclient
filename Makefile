.DEFAULT_GOAL := all
isort = isort hs_rdf tests
black = black -S -l 120 --target-version py38 hs_rdf tests

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: install
install:
	pip install -r requirements.txt
