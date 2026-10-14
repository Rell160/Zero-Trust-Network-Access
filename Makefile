.PHONY: help dev-up dev-down dev-logs test lint format clean install

help:
	@echo "Available targets:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make dev-up     - Start all services with Docker Compose"
	@echo "  make dev-down   - Stop all services"
	@echo "  make dev-logs   - Follow service logs"
	@echo "  make test       - Run pytest test suite"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Auto-format code with ruff"
	@echo "  make clean      - Remove caches and temp files"

install:
	pip install -r requirements.txt

dev-up:
	docker compose up -d --build

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f

test:
	python -m pytest tests/ -v --tb=short

lint:
	python -m ruff check src/ tests/

format:
	python -m ruff format src/ tests/

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]" 2>nul || true
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]" 2>nul || true
	python -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]" 2>nul || true
