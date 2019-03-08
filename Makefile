.PHONY: help prepare-dev test lint run doc

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3

SOURCEDIR := src/
SOURCES := $(shell find $(SOURCEDIR) -name '*.py')
PROJECT_NAME := $(shell python setup.py --name)
PROJECT_VERSION := $(shell python setup.py --version)
SHELL := /bin/bash

.DEFAULT: help
help:
	@echo "make prepare-dev"
	@echo "       prepare development environment, use only once"
	@echo "make test"
	@echo "       run tests"
	@echo "make lint"
	@echo "       run pylint and mypy"
	@echo "make run"
	@echo "       run project"
	@echo "make doc"
	@echo "       build sphinx documentation"

prepare-dev:
	sudo apt-get -y install python3.5 python3-pip
	#python3 -m pip install virtualenv
	make venv

# Requirements are in setup.py, so whenever setup.py is changed, re-run installation of dependencies.
venv: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: setup.py
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -e .
	${PYTHON} -m pip install -r requirements.txt
	#touch $(VENV_NAME)/bin/activate


#test: venv
#	${PYTHON} -m pytest

lint: venv
	@echo -e "$(BOLD)analyzing code for $(PROJECT_NAME) $(PROJECT_VERSION)$(RESET)"
	-@pylint main.py $(SOURCES)\
		--output-format text --reports no \
		--msg-template "{path}:{line:04d}:{obj} {msg} ({msg_id})"

run: venv
	${PYTHON} main.py Original/

doc: venv
	$(VENV_ACTIVATE); sphinx-apidoc -o docs/rst/ src/; cd docs; make clean; make html
