# Makefile for Molecular Data Management and CRO Integration Platform
#
# This Makefile provides standardized commands for development, testing, deployment,
# and infrastructure management. It serves as the main entry point for developers to interact 
# with the project's build and deployment processes.

# Default environment variables that can be overridden
ENVIRONMENT := $(or $(ENV),dev)
AWS_REGION := $(or $(AWS_REGION),us-east-1)
IMAGE_TAG := $(or $(IMAGE_TAG),latest)
DOCKER_REGISTRY := $(or $(DOCKER_REGISTRY),molecule-flow)

# Declare all targets as phony (not representing files)
.PHONY: help setup build build-frontend build-backend up down restart logs test test-backend test-frontend test-integration test-performance lint lint-backend lint-frontend format format-backend format-frontend migrate seed-db reset-db shell-backend shell-frontend shell-db deploy deploy-backend deploy-frontend deploy-workers infra-init infra-plan infra-apply infra-destroy clean

# Default target when running make without arguments
all: help

# Display help information about available make commands
help:
	@echo "Molecular Data Management and CRO Integration Platform"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  setup              Set up the development environment"
	@echo "  build              Build all Docker containers"
	@echo "  build-frontend     Build only the frontend container"
	@echo "  build-backend      Build only the backend container"
	@echo "  up                 Start all containers in development mode"
	@echo "  down               Stop all containers"
	@echo "  restart            Restart all containers"
	@echo "  logs               View logs from all containers"
	@echo ""
	@echo "Testing:"
	@echo "  test               Run all tests"
	@echo "  test-backend       Run backend tests"
	@echo "  test-frontend      Run frontend tests"
	@echo "  test-integration   Run integration tests"
	@echo "  test-performance   Run performance tests using k6"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint               Run linting on all code"
	@echo "  lint-backend       Run linting on backend code"
	@echo "  lint-frontend      Run linting on frontend code"
	@echo "  format             Format all code according to style guidelines"
	@echo "  format-backend     Format backend code"
	@echo "  format-frontend    Format frontend code"
	@echo ""
	@echo "Database:"
	@echo "  migrate            Run database migrations"
	@echo "  seed-db            Seed the database with initial data"
	@echo "  reset-db           Reset the database (drop and recreate)"
	@echo ""
	@echo "Shell Access:"
	@echo "  shell-backend      Open a shell in the backend container"
	@echo "  shell-frontend     Open a shell in the frontend container"
	@echo "  shell-db           Open a PostgreSQL shell in the database container"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy             Deploy all services to the specified environment"
	@echo "  deploy-backend     Deploy only the backend service"
	@echo "  deploy-frontend    Deploy only the frontend service"
	@echo "  deploy-workers     Deploy only the worker services"
	@echo ""
	@echo "Infrastructure:"
	@echo "  infra-init         Initialize Terraform for infrastructure management"
	@echo "  infra-plan         Generate and show Terraform execution plan"
	@echo "  infra-apply        Apply Terraform changes to create/update infrastructure"
	@echo "  infra-destroy      Destroy Terraform-managed infrastructure"
	@echo ""
	@echo "Utilities:"
	@echo "  clean              Clean up development environment"
	@echo ""
	@echo "Environment Variables:"
	@echo "  ENV                Target environment (default: dev)"
	@echo "  AWS_REGION         AWS region (default: us-east-1)"
	@echo "  IMAGE_TAG          Docker image tag (default: latest)"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                    # Set up development environment"
	@echo "  make build                    # Build all containers"
	@echo "  make up                       # Start all containers"
	@echo "  make deploy ENV=staging       # Deploy to staging environment"
	@echo "  make infra-apply ENV=prod     # Apply infrastructure changes to production"

# Set up the development environment
setup:
	@echo "Setting up development environment..."
	@if ! command -v docker > /dev/null; then \
		echo "Error: Docker not installed. Please install Docker first."; \
		exit 1; \
	fi
	@if ! command -v docker-compose > /dev/null; then \
		echo "Error: Docker Compose not installed. Please install Docker Compose first."; \
		exit 1; \
	fi
	@mkdir -p data/postgres data/redis data/molecules
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "Created .env file from .env.example"; \
		else \
			echo "Warning: .env.example not found. Please create a .env file manually."; \
		fi \
	fi
	@if [ -f ./infrastructure/scripts/bootstrap.sh ]; then \
		echo "Running bootstrap script..."; \
		chmod +x ./infrastructure/scripts/bootstrap.sh; \
		./infrastructure/scripts/bootstrap.sh --environment $(ENVIRONMENT); \
	else \
		echo "Warning: Bootstrap script not found. Skipping infrastructure setup."; \
	fi
	@make build
	@echo "Development environment setup complete!"

# Build all Docker containers
build: build-frontend build-backend
	@echo "All Docker containers built successfully!"

# Build only the frontend container
build-frontend:
	@echo "Building frontend container..."
	@docker-compose build frontend

# Build only the backend container
build-backend:
	@echo "Building backend containers..."
	@docker-compose build backend molecule_service worker

# Start all containers in development mode
up:
	@echo "Starting containers in development mode..."
	@docker-compose up -d
	@echo "Containers started. Use 'make logs' to view logs."

# Stop all containers
down:
	@echo "Stopping containers..."
	@docker-compose down
	@echo "Containers stopped."

# Restart all containers
restart:
	@echo "Restarting containers..."
	@docker-compose restart
	@echo "Containers restarted."

# View logs from all containers
logs:
	@echo "Viewing logs from all containers (press Ctrl+C to exit)..."
	@docker-compose logs -f

# Run all tests
test: test-backend test-frontend test-integration
	@echo "All tests completed!"

# Run backend tests
test-backend:
	@echo "Running backend tests..."
	@docker-compose run --rm backend pytest

# Run frontend tests
test-frontend:
	@echo "Running frontend tests..."
	@docker-compose run --rm frontend npm test

# Run integration tests
test-integration:
	@echo "Running integration tests..."
	@if ! docker-compose ps | grep -q "Up"; then \
		echo "Containers not running. Starting containers first..."; \
		make up; \
		echo "Waiting for services to be ready..."; \
		sleep 10; \
	fi
	@docker-compose run --rm backend pytest tests/integration

# Run performance tests using k6
test-performance:
	@echo "Running performance tests with k6..."
	@if ! command -v k6 > /dev/null; then \
		echo "Error: k6 not installed. Please install k6 first."; \
		exit 1; \
	fi
	@if ! docker-compose ps | grep -q "Up"; then \
		echo "Containers not running. Starting containers first..."; \
		make up; \
		echo "Waiting for services to be ready..."; \
		sleep 10; \
	fi
	@k6 run tests/performance/load-test.js

# Run linting on all code
lint: lint-backend lint-frontend
	@echo "Linting completed!"

# Run linting on backend code
lint-backend:
	@echo "Linting backend code..."
	@docker-compose run --rm backend flake8

# Run linting on frontend code
lint-frontend:
	@echo "Linting frontend code..."
	@docker-compose run --rm frontend npm run lint

# Format all code according to style guidelines
format: format-backend format-frontend
	@echo "Code formatting completed!"

# Format backend code
format-backend:
	@echo "Formatting backend code..."
	@docker-compose run --rm backend black .

# Format frontend code
format-frontend:
	@echo "Formatting frontend code..."
	@docker-compose run --rm frontend npm run format

# Run database migrations
migrate:
	@echo "Running database migrations..."
	@docker-compose run --rm backend alembic upgrade head
	@echo "Migrations completed!"

# Seed the database with initial data
seed-db:
	@echo "Seeding database with initial data..."
	@docker-compose run --rm backend python -m scripts.seed_db
	@echo "Database seeded!"

# Reset the database (drop and recreate)
reset-db:
	@echo "Warning: This will delete all data in the database!"
	@read -p "Are you sure you want to continue? [y/N] " confirm && \
		[ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ] || exit 1
	@echo "Resetting database..."
	@docker-compose down -v database
	@docker-compose up -d database
	@echo "Waiting for database to be ready..."
	@sleep 5
	@make migrate
	@echo "Database reset complete!"

# Open a shell in the backend container
shell-backend:
	@echo "Opening shell in backend container..."
	@docker-compose exec backend /bin/bash || \
		echo "Error: Backend container is not running. Use 'make up' to start containers."

# Open a shell in the frontend container
shell-frontend:
	@echo "Opening shell in frontend container..."
	@docker-compose exec frontend /bin/sh || \
		echo "Error: Frontend container is not running. Use 'make up' to start containers."

# Open a PostgreSQL shell in the database container
shell-db:
	@echo "Opening PostgreSQL shell in database container..."
	@docker-compose exec database psql -U postgres -d molecule_platform || \
		echo "Error: Database container is not running. Use 'make up' to start containers."

# Deploy all services to the specified environment
deploy: deploy-backend deploy-frontend deploy-workers
	@echo "All services deployed to $(ENVIRONMENT) environment!"

# Deploy only the backend service
deploy-backend:
	@echo "Deploying backend service to $(ENVIRONMENT) environment..."
	@if [ -f ./deployment/scripts/deploy_backend.sh ]; then \
		chmod +x ./deployment/scripts/deploy_backend.sh; \
		./deployment/scripts/deploy_backend.sh --environment $(ENVIRONMENT) --image-tag $(IMAGE_TAG); \
	else \
		echo "Error: Backend deployment script not found."; \
		exit 1; \
	fi

# Deploy only the frontend service
deploy-frontend:
	@echo "Deploying frontend service to $(ENVIRONMENT) environment..."
	@if [ -f ./deployment/scripts/deploy_frontend.sh ]; then \
		chmod +x ./deployment/scripts/deploy_frontend.sh; \
		./deployment/scripts/deploy_frontend.sh --environment $(ENVIRONMENT) --image-tag $(IMAGE_TAG); \
	else \
		echo "Error: Frontend deployment script not found."; \
		exit 1; \
	fi

# Deploy only the worker services
deploy-workers:
	@echo "Deploying worker services to $(ENVIRONMENT) environment..."
	@if [ -f ./deployment/scripts/deploy_workers.sh ]; then \
		chmod +x ./deployment/scripts/deploy_workers.sh; \
		./deployment/scripts/deploy_workers.sh --environment $(ENVIRONMENT) --image-tag $(IMAGE_TAG); \
	else \
		echo "Error: Worker deployment script not found."; \
		exit 1; \
	fi

# Initialize Terraform for infrastructure management
infra-init:
	@echo "Initializing Terraform for $(ENVIRONMENT) environment..."
	@if [ -d infrastructure/terraform/environments/$(ENVIRONMENT) ]; then \
		cd infrastructure/terraform/environments/$(ENVIRONMENT) && terraform init; \
	else \
		echo "Error: Terraform environment directory not found."; \
		exit 1; \
	fi

# Generate and show Terraform execution plan
infra-plan:
	@echo "Generating Terraform execution plan for $(ENVIRONMENT) environment..."
	@if [ -d infrastructure/terraform/environments/$(ENVIRONMENT) ]; then \
		cd infrastructure/terraform/environments/$(ENVIRONMENT) && terraform plan; \
	else \
		echo "Error: Terraform environment directory not found."; \
		exit 1; \
	fi

# Apply Terraform changes to create/update infrastructure
infra-apply:
	@echo "Warning: This will modify infrastructure in the $(ENVIRONMENT) environment!"
	@read -p "Are you sure you want to continue? [y/N] " confirm && \
		[ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ] || exit 1
	@echo "Applying Terraform changes for $(ENVIRONMENT) environment..."
	@if [ -d infrastructure/terraform/environments/$(ENVIRONMENT) ]; then \
		cd infrastructure/terraform/environments/$(ENVIRONMENT) && terraform apply; \
	else \
		echo "Error: Terraform environment directory not found."; \
		exit 1; \
	fi

# Destroy Terraform-managed infrastructure
infra-destroy:
	@echo "Warning: This will DESTROY ALL INFRASTRUCTURE in the $(ENVIRONMENT) environment!"
	@echo "This action is IRREVERSIBLE and will result in DATA LOSS!"
	@read -p "Type 'destroy' to confirm: " confirm && \
		[ "$$confirm" = "destroy" ] || exit 1
	@echo "Destroying Terraform-managed infrastructure for $(ENVIRONMENT) environment..."
	@if [ -d infrastructure/terraform/environments/$(ENVIRONMENT) ]; then \
		cd infrastructure/terraform/environments/$(ENVIRONMENT) && terraform destroy; \
	else \
		echo "Error: Terraform environment directory not found."; \
		exit 1; \
	fi

# Clean up development environment
clean:
	@echo "Warning: This will remove all containers, volumes, and data!"
	@read -p "Are you sure you want to continue? [y/N] " confirm && \
		[ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ] || exit 1
	@echo "Cleaning up development environment..."
	@docker-compose down -v
	@docker-compose rm -f
	@rm -rf data/postgres/* data/redis/* data/molecules/*
	@echo "Development environment cleaned up!"