PYTHON = python3
PIP = pip3
MAIN = main.py
MAP ?= maps/easy/01_linear_path.txt

.PHONY: help install run debug test lint typecheck clean re

help:
	@echo "Available commands:"
	@echo "  make install          Install dependencies"
	@echo "  make run MAP=<file>   Run the project"
	@echo "  make debug MAP=<file> Run with debug output"
	@echo "  make test             Run basic syntax checks"
	@echo "  make lint             Run flake8"
	@echo "  make typecheck        Run mypy"
	@echo "  make clean            Remove Python cache files"
	@echo "  make re               Clean then run"

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) $(MAIN) $(MAP)

debug:
	$(PYTHON) $(MAIN) $(MAP) --debug

test:
	$(PYTHON) -m compileall .

lint:
	flake8 .

typecheck:
	mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

re: clean run