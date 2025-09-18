# Makefile for TACC Tools

.PHONY: help install install-dev test lint format clean build containers docs

help:
	@echo "TACC Tools - Available commands:"
	@echo "  install      - Install package"
	@echo "  install-dev  - Install package in development mode with all extras"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  containers   - Build all containers"
	@echo "  docs         - Generate documentation"

install:
	pip install .

install-dev:
	pip install -e ".[dev,ros1,ros2,visualization,remote]"

test:
	pytest tests/ -v

lint:
	flake8 tacc_tools/
	mypy tacc_tools/

format:
	black tacc_tools/ tests/ examples/

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f *.sif

build: clean
	python -m build

containers:
	@echo "Building download container..."
	apptainer build rosbag_downloader.sif tacc_tools/containers/rosbag_downloader.def
	@echo "Building visualization container..."
	apptainer build rosbag_visualizer.sif tacc_tools/containers/rosbag_visualizer.def
	@echo "Containers built successfully!"

docs:
	@echo "Documentation generation not implemented yet"
	@echo "See README.md for usage instructions"

# Development helpers
check: lint test
	@echo "All checks passed!"

setup-dev: install-dev
	@echo "Development environment setup complete!"