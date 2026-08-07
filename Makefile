# Reproduction pipeline. On Windows without make, run the same commands
# directly (see README "Reproduction").

PYTHON ?= .venv/Scripts/python
ifeq ($(OS),)
PYTHON := .venv/bin/python
endif

.PHONY: all data analysis backtest paper test

all: data analysis backtest paper

data:
	$(PYTHON) scripts/download_data.py

analysis:
	$(PYTHON) scripts/run_analysis.py

backtest:
	$(PYTHON) scripts/run_backtest.py

paper:
	$(PYTHON) scripts/generate_paper_outputs.py

test:
	$(PYTHON) -m pytest tests/
