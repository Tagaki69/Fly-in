PYTHON = python3
PIP = pip3
MAIN = main.py

MAP ?= maps/easy/01_linear_path.txt
MAX_PATHS ?= 5

.PHONY: help install run debug visual visual-debug test lint typecheck clean re

help:
	@echo "Available commands:"
	@echo "  make install                         Install dependencies"
	@echo "  make run MAP=<file>                  Run normal mode"
	@echo "  make debug MAP=<file>                Run debug mode"
	@echo "  make visual MAP=<file>               Run Pygame visualizer"
	@echo "  make visual-debug MAP=<file>         Run debug + Pygame visualizer"
	@echo "  make run MAX_PATHS=3                 Run with custom max paths"
	@echo "  make test                            Run Python syntax checks"
	@echo "  make lint                            Run flake8"
	@echo "  make clean                           Remove cache files"
	@echo "  make re                              Clean then run"

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) $(MAIN) $(MAP) --max-paths $(MAX_PATHS)

debug:
	$(PYTHON) $(MAIN) $(MAP) --debug --max-paths $(MAX_PATHS)

visual:
	$(PYTHON) $(MAIN) $(MAP) --visual --max-paths $(MAX_PATHS)

visual-debug:
	$(PYTHON) $(MAIN) $(MAP) --visual --debug --max-paths $(MAX_PATHS)

test:
	$(PYTHON) -m compileall .

lint:
	flake8 .
	mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

re: clean run