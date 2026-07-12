# HealthWatch-Backend - Testing Automation
# ========================================

# Variables
PYTHON = venv/Scripts/python.exe
PYTEST = $(PYTHON) -m pytest
PYTEST_OPTS = -v --tb=short

# ---- Comandos principales ----

.PHONY: test
test: ## Ejecutar todos los tests
	$(PYTEST) $(PYTEST_OPTS)

.PHONY: test-unit
test-unit: ## Ejecutar solo tests unitarios
	$(PYTEST) tests/unit/ $(PYTEST_OPTS)

.PHONY: test-integration
test-integration: ## Ejecutar solo tests de integración
	$(PYTEST) tests/integration/ $(PYTEST_OPTS)

.PHONY: test-coverage
test-coverage: ## Ejecutar tests con cobertura de código
	$(PYTEST) --cov=app --cov-report=term-missing --cov-report=html

.PHONY: test-verbose
test-verbose: ## Ejecutar tests con output verbose
	$(PYTEST) -v -s

.PHONY: test-rerun
test-rerun: ## Re-ejecutar solo tests fallidos
	$(PYTEST) --lf

.PHONY: test-marker
test-marker: ## Ejecutar tests por marker (ej: make test-marker MARKER=unit)
	$(PYTEST) -m $(MARKER) $(PYTEST_OPTS)

# ---- Reportes de cobertura ----

.PHONY: coverage-html
coverage-html: ## Generar reporte HTML de cobertura
	$(PYTEST) --cov=app --cov-report=html
	@echo "Reporte generado en htmlcov/index.html"

.PHONY: coverage-check
coverage-check: ## Verificar que cobertura >= 70%
	$(PYTEST) --cov=app --cov-fail-under=70 -q

# ---- Utilidades ----

.PHONY: test-install
test-install: ## Instalar dependencias de testing
	$(PYTHON) -m pip install -r requirements.txt

.PHONY: test-clean
test-clean: ## Limpiar caché de pytest
	Remove-Item -Recurse -Force .pytest_cache, tests/__pycache__, tests/unit/__pycache__, tests/integration/__pycache__ -ErrorAction SilentlyContinue

.PHONY: help
help: ## Mostrar esta ayuda
	@echo "Uso: make <comando>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
