# =============================================================================
# Project Configuration
# =============================================================================
PROJECT_NAME := wyrestorm_networkhd
PROJECT_DISPLAY_NAME := wyrestorm-networkhd-ha
COMPONENT_PATH := custom_components/wyrestorm_networkhd

# Virtual environment configuration
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip

# Development tools (use venv versions in CI, system versions locally as fallback)
RUFF := $(shell if [ -x "$(VENV_BIN)/ruff" ]; then echo "$(VENV_BIN)/ruff"; else echo "ruff"; fi)
MYPY := $(shell if [ -x "$(VENV_BIN)/mypy" ]; then echo "$(VENV_BIN)/mypy"; else echo "mypy"; fi)
BANDIT := $(shell if [ -x "$(VENV_BIN)/bandit" ]; then echo "$(VENV_BIN)/bandit"; else echo "bandit"; fi)
PYTEST := $(shell if [ -x "$(VENV_BIN)/pytest" ]; then echo "$(VENV_BIN)/pytest"; else echo "pytest"; fi)
PRE_COMMIT := $(shell if [ -x "$(VENV_BIN)/pre-commit" ]; then echo "$(VENV_BIN)/pre-commit"; else echo "pre-commit"; fi)
VULTURE := $(shell if [ -x "$(VENV_BIN)/vulture" ]; then echo "$(VENV_BIN)/vulture"; else echo "vulture"; fi)
PRETTIER := npx -y prettier@3.3.3

# Better Python detection
PYTHON3 := $(shell command -v python3 2> /dev/null || echo "python3")

# Fallback for systems without python3
ifeq ($(PYTHON3),python3)
    PYTHON3 := python
endif

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Verbosity control
ifeq ($(VERBOSE),1)
    Q :=
    ECHO := @echo
else
    Q := @
    ECHO := @echo
endif

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help \
        install install-deps create-venv update-deps \
        test test-cov \
        format format-code format-check prettier-check lint type-check \
        security-check code-quality check \
        clean clean-all clean-build clean-pyc clean-test clean-cache \
        health-check check-project-structure check-versions show-deps \
        setup-pre-commit pre-commit validate-config ensure-venv \
        dev-workflow ha-check

# =============================================================================
# Help Target
# =============================================================================
help: ## Show this help message
	@echo "$(BLUE)Available commands for $(PROJECT_DISPLAY_NAME):$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start:$(NC)"
	@echo "  install          - Complete development environment setup"
	@echo "  dev-workflow     - Format → Lint → Fast Tests (daily development)"
	@echo "  health-check     - Comprehensive project validation"
	@echo ""
	@echo "$(YELLOW)📦 Development Setup:$(NC)"
	@echo "  create-venv      - Create/ensure virtual environment"
	@echo "  install-deps     - Install development dependencies"
	@echo "  update-deps      - Update all dependencies"
	@echo "  setup-pre-commit - Install pre-commit hooks"
	@echo ""
	@echo "$(YELLOW)🧪 Testing:$(NC)"
	@echo "  test             - Run all tests"
	@echo "  test-cov         - Run all tests with coverage report"
	@echo ""
	@echo "$(YELLOW)✨ Code Formatting:$(NC)"
	@echo "  format           - Format all code"
	@echo "  format-code      - Format Python code (Ruff)"
	@echo "  format-check     - Check if code is properly formatted"
	@echo "  prettier-check   - Check JSON, YAML and Markdown formatting (Prettier)"
	@echo ""
	@echo "$(YELLOW)🔍 Code Quality:$(NC)"
	@echo "  check            - Run all quality checks"
	@echo "  lint             - Run linting checks (Ruff)"
	@echo "  type-check       - Run type checking with MyPy"
	@echo "  code-quality     - Run dead-code checks (Vulture)"
	@echo "  security-check   - Run security checks (Bandit)"
	@echo ""
	@echo "$(YELLOW)🏠 Home Assistant:$(NC)"
	@echo "  ha-check         - Validate Home Assistant component"
	@echo ""
	@echo "$(YELLOW)🧹 Cleanup:$(NC)"
	@echo "  clean            - Remove all build artifacts"
	@echo "  clean-all        - Remove everything including venv"
	@echo ""
	@echo "$(YELLOW)🔧 Utilities:$(NC)"
	@echo "  health-check     - Comprehensive project validation"
	@echo "  show-deps        - Show installed dependencies"
	@echo "  check-versions   - Check Python and package versions"
	@echo "  pre-commit       - Setup and run pre-commit hooks"

# =============================================================================
# Quick Start Targets
# =============================================================================
install: validate-config create-venv install-deps setup-pre-commit ## Complete development environment setup
	@echo ""
	@echo "$(GREEN)🎉 Setup complete! Next steps:$(NC)"
	@echo "  1. Activate: source $(VENV_DIR)/bin/activate"
	@echo "  2. Check health: make health-check"
	@echo "  3. Start testing: make test"

dev-workflow: format check test ## Complete development workflow (format, check, tests)
	@echo "$(GREEN)✓$(NC) Development workflow completed"

health-check: check-versions show-deps check-project-structure format-check test-cov check ## Comprehensive project validation
	@echo ""
	@echo "$(GREEN)🎉 Health check complete - all systems validated!$(NC)"

# =============================================================================
# Development Setup
# =============================================================================
create-venv: ## Create/ensure virtual environment
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)📦 Creating virtual environment...$(NC)"; \
		$(PYTHON3) -m venv $(VENV_DIR); \
		echo "$(GREEN)✓$(NC) Virtual environment created"; \
	else \
		echo "$(GREEN)✓$(NC) Virtual environment already exists"; \
	fi


install-deps: create-venv ## Install development dependencies
	$(ECHO) "$(YELLOW)🔧 Installing development dependencies...$(NC)"
	$(Q)$(PIP) install --upgrade pip setuptools
	$(Q)$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓$(NC) Development dependencies installed"

update-deps: install-deps ## Update all dependencies
	@echo "$(GREEN)✓$(NC) Dependencies updated"

setup-pre-commit: install-deps ## Install pre-commit hooks
	$(ECHO) "$(YELLOW)📝 Installing pre-commit hooks...$(NC)"
	$(Q)$(PRE_COMMIT) install
	@echo "$(GREEN)✓$(NC) Pre-commit hooks installed"

# =============================================================================
# Testing
# =============================================================================
test: ## Run all tests
	$(ECHO) "$(YELLOW)Running all tests...$(NC)"
	$(Q)$(PYTEST) tests/ -v
	@echo "$(GREEN)✓$(NC) All tests completed"

test-cov: ## Run all tests with coverage
	$(ECHO) "$(YELLOW)Running all tests with coverage...$(NC)"
	$(Q)$(PYTEST) tests/ -v  # coverage options are in pyproject.toml
	@echo "$(GREEN)✓$(NC) Coverage report generated (see htmlcov/index.html)"

# =============================================================================
# Code Formatting
# =============================================================================
format: format-code ## Format all code

format-check: ## Check if code is properly formatted (without fixing)
	$(ECHO) "$(YELLOW)Checking code formatting...$(NC)"
	$(Q)$(RUFF) format --check $(COMPONENT_PATH)/ tests/
	@echo "$(GREEN)✓$(NC) Code formatting verified"

format-code: ## Format Python code
	$(ECHO) "$(YELLOW)Formatting Python code...$(NC)"
	$(Q)$(RUFF) format $(COMPONENT_PATH)/ tests/
	$(Q)$(RUFF) check --fix $(COMPONENT_PATH)/ tests/
	@echo "$(GREEN)✓$(NC) Python code formatted"

prettier-check: ## Check JSON, YAML and Markdown formatting (needs Node.js)
	$(ECHO) "$(YELLOW)Checking Prettier formatting...$(NC)"
	$(Q)$(PRETTIER) --check .
	@echo "$(GREEN)✓$(NC) Prettier formatting verified"

# =============================================================================
# Code Quality & Linting
# =============================================================================
check: lint type-check prettier-check code-quality security-check ## Run all code quality checks
	@echo "$(GREEN)✅ All code quality checks completed$(NC)"

lint: ## Run linting checks
	$(ECHO) "$(YELLOW)Running linting...$(NC)"
	$(Q)$(RUFF) check $(COMPONENT_PATH)/ tests/
	@echo "$(GREEN)✓$(NC) Linting completed"

type-check: ## Run type checking with MyPy
	$(ECHO) "$(YELLOW)Running type checks...$(NC)"
	$(Q)$(MYPY) $(COMPONENT_PATH)/  # strict, see pyproject.toml
	@echo "$(GREEN)✓$(NC) Type checking completed"

code-quality: ## Run additional code quality checks
	$(ECHO) "$(YELLOW)Running code quality checks...$(NC)"
	$(Q)$(VULTURE) $(COMPONENT_PATH)/ --min-confidence 80 --ignore-names config,entry_data,addr  # unused HA callback arguments
	@echo "$(GREEN)✓$(NC) Code quality checks completed"

security-check: ## Run security checks
	$(ECHO) "$(YELLOW)Running security checks...$(NC)"
	$(Q)$(BANDIT) -r $(COMPONENT_PATH)/ -f json -o security-report.json
	@echo "$(GREEN)✓$(NC) Security checks completed"

# =============================================================================
# Home Assistant Specific
# =============================================================================
ha-check: ## Validate Home Assistant component
	$(ECHO) "$(YELLOW)Validating Home Assistant component...$(NC)"
	@if [ -f "$(COMPONENT_PATH)/manifest.json" ]; then \
		echo "$(GREEN)✓$(NC) manifest.json found"; \
		$(PYTHON3) -c "import json; json.load(open('$(COMPONENT_PATH)/manifest.json'))" && echo "$(GREEN)✓$(NC) manifest.json is valid JSON"; \
	else \
		echo "$(RED)✗$(NC) manifest.json not found"; \
		exit 1; \
	fi
	@if [ -f "$(COMPONENT_PATH)/__init__.py" ]; then \
		echo "$(GREEN)✓$(NC) __init__.py found"; \
	else \
		echo "$(RED)✗$(NC) __init__.py not found"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓$(NC) Home Assistant component validation passed"


# =============================================================================
# Cleanup
# =============================================================================
clean: clean-build clean-pyc clean-test clean-cache ## Remove all build artifacts

clean-all: clean ## Remove everything including venv
	$(ECHO) "$(YELLOW)Removing virtual environment...$(NC)"
	$(Q)rm -rf $(VENV_DIR)
	@echo "$(GREEN)✓$(NC) Complete cleanup finished"

clean-build: ## Remove build artifacts
	$(ECHO) "$(YELLOW)Cleaning build artifacts...$(NC)"
	$(Q)rm -rf build/ dist/
	$(Q)find . -name '*.egg-info' -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓$(NC) Build artifacts cleaned"

clean-pyc: ## Remove Python cache files
	$(ECHO) "$(YELLOW)Cleaning Python cache files...$(NC)"
	$(Q)find . -name '*.pyc' -delete
	$(Q)find . -name '*.pyo' -delete
	$(Q)find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓$(NC) Python cache cleaned"

clean-test: ## Remove test artifacts
	$(ECHO) "$(YELLOW)Cleaning test artifacts...$(NC)"
	$(Q)rm -rf .pytest_cache/ htmlcov/ coverage.xml
	$(Q)find . -name '.coverage*' -type f -delete 2>/dev/null || true
	@echo "$(GREEN)✓$(NC) Test artifacts cleaned"

clean-cache: ## Remove tool cache files
	$(ECHO) "$(YELLOW)Cleaning tool caches...$(NC)"
	$(Q)rm -rf .ruff_cache/ .mypy_cache/
	@echo "$(GREEN)✓$(NC) Tool caches cleaned"

# =============================================================================
# Utilities
# =============================================================================
show-deps: ## Show installed dependencies
	@echo "$(YELLOW)Installed dependencies:$(NC)"
	@if [ -x "$(PIP)" ]; then \
		$(PIP) list; \
	else \
		echo "$(YELLOW)⚠ Virtual environment not found - run 'make install' first$(NC)"; \
		exit 1; \
	fi

check-versions: ## Check Python and package versions
	@echo "$(YELLOW)Version information:$(NC)"
	@$(PYTHON3) -c "import sys; print('$(GREEN)Python:$(NC) ' + sys.version)"
	@if [ -x "$(PYTHON)" ]; then \
		PYTHONPATH=. $(PYTHON) -c "import sys; sys.path.insert(0, '.'); print('$(GREEN)✓$(NC) Python environment ready')" 2>/dev/null || echo "$(YELLOW)⚠$(NC) Python environment needs setup"; \
	fi

pre-commit: setup-pre-commit ## Setup, update and run pre-commit hooks
	$(ECHO) "$(YELLOW)Updating and running pre-commit...$(NC)"
	$(Q)$(PRE_COMMIT) autoupdate
	$(Q)$(PRE_COMMIT) run --all-files
	@echo "$(GREEN)✓$(NC) Pre-commit completed"

# =============================================================================
# Internal/Support Targets
# =============================================================================
validate-config: ## Validate project configuration
	@echo "$(YELLOW)Validating project configuration...$(NC)"
	@if [ -f "pyproject.toml" ]; then \
		echo "$(GREEN)✓$(NC) pyproject.toml found"; \
	else \
		echo "$(RED)✗$(NC) pyproject.toml not found"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓$(NC) Configuration validated"

ensure-venv: ## Ensure virtual environment exists
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make install' first.$(NC)"; \
		exit 1; \
	fi

check-project-structure: ## Validate project structure and required files
	@echo "$(YELLOW)Project Structure Validation:$(NC)"
	@FAILED=0; \
	if [ -d "$(COMPONENT_PATH)" ]; then echo "$(GREEN)✓$(NC) Custom component directory exists"; else echo "$(RED)✗$(NC) Custom component directory missing"; FAILED=1; fi; \
	if [ -d "tests" ]; then echo "$(GREEN)✓$(NC) Tests directory exists"; else echo "$(RED)✗$(NC) Tests directory missing"; FAILED=1; fi; \
	if [ -f "README.md" ]; then echo "$(GREEN)✓$(NC) README.md exists"; else echo "$(RED)✗$(NC) README.md missing"; FAILED=1; fi; \
	if [ -f "$(COMPONENT_PATH)/manifest.json" ]; then echo "$(GREEN)✓$(NC) manifest.json exists"; else echo "$(RED)✗$(NC) manifest.json missing"; FAILED=1; fi; \
	if [ -f "$(COMPONENT_PATH)/__init__.py" ]; then echo "$(GREEN)✓$(NC) Component __init__.py exists"; else echo "$(RED)✗$(NC) Component __init__.py missing"; FAILED=1; fi; \
	if [ $$FAILED -eq 1 ]; then echo "$(RED)✗$(NC) Project structure validation failed"; exit 1; else echo "$(GREEN)✓$(NC) Project structure validation passed"; fi