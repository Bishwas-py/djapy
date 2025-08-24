# Makefile for sample djapy project

.PHONY: test test-verbose test-coverage migrate runserver install help

# Default target
help:
	@echo "Available commands:"
	@echo "  test          - Run all tests"
	@echo "  test-verbose  - Run tests with verbose output"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  migrate       - Run Django migrations"
	@echo "  runserver     - Start Django development server"
	@echo "  install       - Install dependencies"
	@echo "  clean         - Clean up temporary files"

# Run tests
test:
	@echo "🧪 Running tests..."
	python manage.py test api.tests --verbosity=1

# Run tests with verbose output
test-verbose:
	@echo "🧪 Running tests with verbose output..."
	python manage.py test api.tests --verbosity=2

# Run tests with coverage (requires coverage.py)
test-coverage:
	@echo "🧪 Running tests with coverage..."
	coverage run --source='.' manage.py test api.tests
	coverage report -m
	coverage html

# Run specific test class
test-class:
	@echo "🧪 Running specific test class..."
	@read -p "Enter test class (e.g., api.tests.UserAPITest): " class; \
	python manage.py test $$class --verbosity=2

# Run specific test method
test-method:
	@echo "🧪 Running specific test method..."
	@read -p "Enter test method (e.g., api.tests.UserAPITest.test_create_user_success): " method; \
	python manage.py test $$method --verbosity=2

# Run migrations
migrate:
	@echo "🔄 Running migrations..."
	python manage.py migrate

# Start development server
runserver:
	@echo "🚀 Starting development server..."
	python manage.py runserver

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r ../requirements.txt

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -f .coverage

# Quick development cycle
dev: migrate test runserver

# CI/CD pipeline simulation
ci: install migrate test
