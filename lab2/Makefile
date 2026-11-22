.PHONY: help install test test-e2e test-solid lint typecheck run-desktop run-web run-browser clean

PYTHON ?= python

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies including playwright"
	@echo "  make test         - Run full test suite (50+ tests)"
	@echo "  make test-solid   - Run SOLID architectural tests"
	@echo "  make test-e2e     - Run Playwright E2E browser tests"
	@echo "  make run-desktop  - Launch desktop Tkinter GUI application"
	@echo "  make run-web      - Launch web server on http://127.0.0.1:8000"
	@echo "  make run-browser  - Launch web server with automated Playwright browser"
	@echo "  make clean        - Remove caches and build artifacts"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install pytest pytest-cov playwright
	$(PYTHON) -m playwright install chromium

test:
	$(PYTHON) -m pytest tests/

test-solid:
	$(PYTHON) -m pytest tests/test_solid.py

test-e2e:
	$(PYTHON) -m pytest tests/test_web_e2e_playwright.py

run-desktop:
	$(PYTHON) run.py

run-web:
	$(PYTHON) run_web.py

run-browser:
	$(PYTHON) run_web.py --browser

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
