# GrowWiz Makefile
# Common development tasks and project management

.PHONY: help install install-dev test test-coverage test-integration lint format clean build docs serve deploy backup

# Default target
help:
	@echo "GrowWiz Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  install-all      Install all dependencies including optional ones"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-watch       Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black and isort"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security-check   Run security checks"
	@echo ""
	@echo "Development:"
	@echo "  serve            Start development server"
	@echo "  serve-prod       Start production server"
	@echo "  monitor          Start sensor monitoring"
	@echo "  scrape           Run web scraping"
	@echo ""
	@echo "Documentation:"
	@echo "  docs             Build documentation"
	@echo "  docs-serve       Serve documentation locally"
	@echo ""
	@echo "Deployment:"
	@echo "  build            Build distribution packages"
	@echo "  deploy           Deploy to production"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  backup           Create database backup"
	@echo "  restore          Restore from backup"
	@echo "  logs             Show application logs"
	@echo ""

# Python and pip commands
PYTHON := python
PIP := pip
PYTEST := pytest

# Directories
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist

# Installation targets
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .[dev]

install-all:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .[all]

# Testing targets
test:
	$(PYTEST) $(TEST_DIR) -v

test-unit:
	$(PYTEST) $(TEST_DIR) -v -m "not integration"

test-integration:
	$(PYTEST) $(TEST_DIR) -v -m "integration"

test-coverage:
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

test-watch:
	$(PYTEST) $(TEST_DIR) -f

test-hardware:
	$(PYTEST) $(TEST_DIR) -v -m "hardware"

test-network:
	$(PYTEST) $(TEST_DIR) -v -m "network"

# Code quality targets
lint:
	flake8 $(SRC_DIR) $(TEST_DIR)
	black --check $(SRC_DIR) $(TEST_DIR)
	isort --check-only $(SRC_DIR) $(TEST_DIR)

format:
	black $(SRC_DIR) $(TEST_DIR)
	isort $(SRC_DIR) $(TEST_DIR)

type-check:
	mypy $(SRC_DIR)

security-check:
	bandit -r $(SRC_DIR)
	safety check

# Development server targets
serve:
	$(PYTHON) -m uvicorn server:app --reload --host 0.0.0.0 --port 8000

serve-prod:
	$(PYTHON) -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4

monitor:
	$(PYTHON) $(SRC_DIR)/cli.py monitor --continuous

scrape:
	$(PYTHON) $(SRC_DIR)/cli.py scrape

diagnose:
	$(PYTHON) $(SRC_DIR)/cli.py diagnose --help

automation:
	$(PYTHON) $(SRC_DIR)/cli.py automation

# Documentation targets
docs:
	cd $(DOCS_DIR) && mkdocs build

docs-serve:
	cd $(DOCS_DIR) && mkdocs serve

docs-deploy:
	cd $(DOCS_DIR) && mkdocs gh-deploy

# Build and distribution targets
build: clean
	$(PYTHON) setup.py sdist bdist_wheel

build-docker:
	docker build -t growwiz:latest .

upload-test:
	twine upload --repository testpypi $(DIST_DIR)/*

upload:
	twine upload $(DIST_DIR)/*

# Docker targets
docker-build:
	docker build -t growwiz:latest .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/data:/app/data growwiz:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Deployment targets
deploy-staging:
	@echo "Deploying to staging environment..."
	# Add staging deployment commands here

deploy-production:
	@echo "Deploying to production environment..."
	# Add production deployment commands here

# Raspberry Pi deployment
deploy-pi:
	@echo "Deploying to Raspberry Pi..."
	rsync -avz --exclude='.git' --exclude='__pycache__' . pi@raspberrypi.local:~/growwiz/
	ssh pi@raspberrypi.local 'cd ~/growwiz && make install && sudo systemctl restart growwiz'

# Database management
db-init:
	$(PYTHON) -c "from src.database import DatabaseManager; db = DatabaseManager(); print('Database initialized')"

db-backup:
	@echo "Creating database backup..."
	mkdir -p backups
	cp data/growwiz.db backups/growwiz_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Backup created in backups/ directory"

db-restore:
	@echo "Available backups:"
	@ls -la backups/
	@echo "To restore, run: cp backups/[backup_file] data/growwiz.db"

# Maintenance targets
clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf *.egg-info
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov
	rm -rf .pytest_cache
	rm -rf .mypy_cache

clean-logs:
	rm -f logs/*.log
	rm -f logs/*.log.*

clean-data:
	@echo "WARNING: This will delete all sensor data and diagnoses!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read
	rm -f data/growwiz.db
	rm -rf uploads/*

# Log management
logs:
	tail -f logs/growwiz.log

logs-error:
	grep ERROR logs/growwiz.log | tail -20

logs-today:
	grep "$(shell date +%Y-%m-%d)" logs/growwiz.log

# System information
info:
	@echo "System Information:"
	@echo "==================="
	@$(PYTHON) -c "import src; src.print_system_info()"

check-deps:
	@echo "Checking dependencies..."
	@$(PYTHON) -c "import src; deps = src.check_dependencies(); print('✓ All good!' if deps['all_satisfied'] else '✗ Missing dependencies')"

# Performance testing
perf-test:
	$(PYTHON) -m pytest $(TEST_DIR) -v -m "slow" --durations=10

load-test:
	locust -f tests/load_test.py --host=http://localhost:8000

# Security and compliance
audit:
	pip-audit
	bandit -r $(SRC_DIR)
	safety check

# Git hooks
install-hooks:
	pre-commit install

run-hooks:
	pre-commit run --all-files

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp .env.example .env; \
		echo "Please edit .env file with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

# Hardware setup (Raspberry Pi)
setup-pi:
	@echo "Setting up Raspberry Pi environment..."
	sudo apt-get update
	sudo apt-get install -y python3-pip python3-venv git
	sudo pip3 install --upgrade pip
	make install-dev
	sudo systemctl enable growwiz
	@echo "Raspberry Pi setup complete"

# Service management (systemd)
install-service:
	sudo cp scripts/growwiz.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable growwiz
	@echo "Service installed. Use 'sudo systemctl start growwiz' to start"

start-service:
	sudo systemctl start growwiz

stop-service:
	sudo systemctl stop growwiz

restart-service:
	sudo systemctl restart growwiz

status-service:
	sudo systemctl status growwiz

# Monitoring and health checks
health-check:
	curl -f http://localhost:8000/health || echo "Service is down"

monitor-system:
	@echo "System monitoring (Press Ctrl+C to stop):"
	@while true; do \
		echo "=== $(shell date) ==="; \
		echo "CPU: $(shell top -bn1 | grep "Cpu(s)" | awk '{print $$2}' | cut -d'%' -f1)%"; \
		echo "Memory: $(shell free | grep Mem | awk '{printf "%.1f%%", $$3/$$2 * 100.0}')"; \
		echo "Disk: $(shell df -h / | awk 'NR==2{print $$5}')"; \
		echo "Temperature: $(shell vcgencmd measure_temp 2>/dev/null || echo 'N/A')"; \
		sleep 5; \
	done

# Data analysis and reporting
generate-report:
	$(PYTHON) scripts/generate_report.py

export-data:
	$(PYTHON) scripts/export_data.py --format csv --output data/export_$(shell date +%Y%m%d).csv

# Backup and restore
full-backup:
	@echo "Creating full system backup..."
	mkdir -p backups/full_$(shell date +%Y%m%d_%H%M%S)
	cp -r data backups/full_$(shell date +%Y%m%d_%H%M%S)/
	cp -r logs backups/full_$(shell date +%Y%m%d_%H%M%S)/
	cp .env backups/full_$(shell date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
	@echo "Full backup created in backups/ directory"

# Development utilities
shell:
	$(PYTHON) -i -c "import src; print('GrowWiz shell ready')"

notebook:
	jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser

# Quick commands for common tasks
quick-test: test-unit
quick-check: lint type-check
quick-start: install serve

# Help for specific components
help-sensors:
	$(PYTHON) $(SRC_DIR)/sensors.py --help

help-classifier:
	$(PYTHON) $(SRC_DIR)/plant_classifier.py --help

help-scraper:
	$(PYTHON) $(SRC_DIR)/scraper.py --help

help-automation:
	$(PYTHON) $(SRC_DIR)/automation.py --help

# Version management
version:
	@$(PYTHON) -c "import src; print(f'GrowWiz v{src.get_version()}')"

bump-version:
	@echo "Current version: $(shell $(PYTHON) -c 'import src; print(src.get_version())')"
	@echo "Bump version with: bumpversion patch|minor|major"

# Project statistics
stats:
	@echo "Project Statistics:"
	@echo "==================="
	@echo "Lines of code:"
	@find $(SRC_DIR) -name "*.py" -exec wc -l {} + | tail -1
	@echo "Test files:"
	@find $(TEST_DIR) -name "*.py" | wc -l
	@echo "Total files:"
	@find . -name "*.py" | wc -l

# Troubleshooting
troubleshoot:
	@echo "GrowWiz Troubleshooting:"
	@echo "========================"
	@echo "1. Check system info:"
	@make info
	@echo ""
	@echo "2. Check dependencies:"
	@make check-deps
	@echo ""
	@echo "3. Check service status:"
	@make health-check
	@echo ""
	@echo "4. Check recent logs:"
	@make logs-error

# All-in-one setup
setup: setup-env install-dev db-init
	@echo "GrowWiz setup complete!"
	@echo "Run 'make serve' to start the development server"

# All-in-one production setup
setup-prod: install db-init install-service
	@echo "GrowWiz production setup complete!"
	@echo "Run 'make start-service' to start the service"