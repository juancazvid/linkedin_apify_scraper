# LinkedIn Scraper Apify Actor - Makefile

.PHONY: help build run test deploy clean install dev lint format

# Default target
help:
	@echo "LinkedIn Scraper Apify Actor - Available Commands:"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make build      - Build Docker image"
	@echo "  make run        - Run actor locally with Docker"
	@echo "  make test       - Run local tests"
	@echo "  make dev        - Run in development mode with docker-compose"
	@echo "  make deploy     - Deploy to Apify platform"
	@echo "  make clean      - Clean up generated files and cache"
	@echo "  make lint       - Run code linting"
	@echo "  make format     - Format code with black"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt
	pip install python-dotenv pytest black flake8

# Build Docker image
build:
	docker build -t linkedin-scraper-actor .

# Run actor locally with Docker
run: build
	docker run --rm \
		-e APIFY_LOCAL_STORAGE_DIR=/tmp/storage \
		-v $(PWD)/storage:/tmp/storage \
		--env-file .env \
		linkedin-scraper-actor

# Run tests
test:
	python test_local.py --mode full

test-function:
	python test_local.py --mode function

# Development mode with docker-compose
dev:
	docker-compose up --build

dev-down:
	docker-compose down

# Deploy to Apify
deploy:
	@echo "Deploying to Apify platform..."
	@command -v apify >/dev/null 2>&1 || { echo "Apify CLI not installed. Run: npm install -g apify-cli"; exit 1; }
	apify push

# Login to Apify
login:
	apify login

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ storage/

# Code quality
lint:
	flake8 src/ --max-line-length=120 --exclude=__pycache__
	flake8 linkedin_scraper/ --max-line-length=120 --exclude=__pycache__

format:
	black src/ --line-length=120
	black linkedin_scraper/ --line-length=120

# Check code formatting
check-format:
	black src/ --check --line-length=120
	black linkedin_scraper/ --check --line-length=120

# Create storage directory
init-storage:
	mkdir -p storage

# View logs
logs:
	tail -f storage/logs/*.log 2>/dev/null || echo "No logs found"

# Environment setup
setup-env:
	@test -f .env || cp .env.example .env
	@echo "Environment file created. Please edit .env with your credentials."

# Full setup for new developers
setup: setup-env install init-storage
	@echo "Setup complete! Edit .env file and run 'make test' to verify."

# Run actor with specific input file
run-input:
	@test -f input.json || { echo "input.json not found. Create it first."; exit 1; }
	docker run --rm \
		-e APIFY_LOCAL_STORAGE_DIR=/tmp/storage \
		-v $(PWD)/storage:/tmp/storage \
		-v $(PWD)/input.json:/usr/src/app/apify_storage/key_value_stores/default/INPUT.json \
		--env-file .env \
		linkedin-scraper-actor

# Check Apify login status
check-login:
	apify info

# Build and push to Apify
release: clean build deploy
	@echo "Release complete!"
