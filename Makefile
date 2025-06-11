# E-commerce Data Warehouse - Makefile
# Automation commands for the dbt data pipeline

.PHONY: help
help: ## Show this help message
	@echo "E-commerce Data Warehouse - Available Commands"
	@echo "=============================================="
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 🐳 Docker Management
docker-up: ## Start all Docker services
	@echo "🚀 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Docker services started"

docker-down: ## Stop all Docker services
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ Docker services stopped"

docker-build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built"

docker-shell: ## Access dbt container shell
	@echo "🐚 Accessing dbt container shell..."
	docker exec -it ecommerce_dbt /bin/bash

docker-logs: ## Show Docker container logs
	docker-compose logs -f

docker-clean: ## Clean up Docker resources
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Docker cleanup completed"

##@ 🗄️ Database Operations
setup-postgres: ## Initialize PostgreSQL schema
	@echo "🏗️ Setting up PostgreSQL schema..."
	docker exec -i postgres_client psql -h $$POSTGRES_HOST -U $$POSTGRES_USER -d $$POSTGRES_DB < scripts/setup_postgres.sql
	@echo "✅ PostgreSQL schema created"

seed-data: ## Generate and load test data into PostgreSQL
	@echo "🌱 Seeding PostgreSQL with test data..."
	docker exec -it postgres_client python /scripts/seed_data.py
	@echo "✅ Test data seeded successfully"

load-snowflake: ## Load data from PostgreSQL to Snowflake
	@echo "📤 Loading data from PostgreSQL to Snowflake..."
	docker exec -it ecommerce_dbt python /app/scripts/loadDataToSnowflake.py
	@echo "✅ Data loaded to Snowflake"

setup-snowflake: ## Configure Snowflake database and schemas
	@echo "❄️ Setting up Snowflake schemas..."
	@echo "Please run the SQL commands in scripts/snowflake_setup.sql manually in your Snowflake console"
	@echo "✅ Snowflake setup instructions provided"

##@ 🔧 dbt Operations
dbt-deps: ## Install dbt package dependencies
	@echo "📦 Installing dbt dependencies..."
	docker exec -it ecommerce_dbt dbt deps
	@echo "✅ dbt dependencies installed"

dbt-debug: ## Debug dbt connection and setup
	@echo "🔍 Debugging dbt setup..."
	docker exec -it ecommerce_dbt dbt debug

dbt-compile: ## Compile dbt models without running
	@echo "⚙️ Compiling dbt models..."
	docker exec -it ecommerce_dbt dbt compile

dbt-run: ## Run all dbt models
	@echo "🏃 Running dbt transformations..."
	docker exec -it ecommerce_dbt dbt run
	@echo "✅ dbt models executed successfully"

dbt-run-staging: ## Run only staging models
	@echo "🏃 Running staging models..."
	docker exec -it ecommerce_dbt dbt run --models staging

dbt-run-core: ## Run only core models
	@echo "🏃 Running core models..."
	docker exec -it ecommerce_dbt dbt run --models marts.core

dbt-run-finance: ## Run only finance models
	@echo "🏃 Running finance models..."
	docker exec -it ecommerce_dbt dbt run --models marts.finance

dbt-test: ## Run all dbt tests
	@echo "🧪 Running dbt tests..."
	docker exec -it ecommerce_dbt dbt test
	@echo "✅ All tests passed"

dbt-test-staging: ## Run tests for staging models only
	@echo "🧪 Testing staging models..."
	docker exec -it ecommerce_dbt dbt test --models staging

dbt-test-core: ## Run tests for core models only
	@echo "🧪 Testing core models..."
	docker exec -it ecommerce_dbt dbt test --models marts.core

dbt-docs: ## Generate and serve dbt documentation
	@echo "📚 Generating dbt documentation..."
	docker exec -it ecommerce_dbt dbt docs generate
	docker exec -d ecommerce_dbt dbt docs serve --port 8080
	@echo "✅ dbt docs available at http://localhost:8080"

dbt-clean: ## Clean dbt artifacts
	@echo "🧹 Cleaning dbt artifacts..."
	docker exec -it ecommerce_dbt dbt clean
	@echo "✅ dbt artifacts cleaned"

dbt-freshness: ## Check source data freshness
	@echo "🕐 Checking source data freshness..."
	docker exec -it ecommerce_dbt dbt source freshness

##@ 🔍 Data Verification
verify-pipeline: ## Verify end-to-end data pipeline
	@echo "🔍 Verifying complete data pipeline..."
	docker exec -it ecommerce_dbt python /app/scripts/verify_data_flow.py
	@echo "✅ Pipeline verification completed"

check-postgres: ## Verify PostgreSQL source data
	@echo "🔍 Checking PostgreSQL data..."
	docker exec -it postgres_client python /scripts/verify_postgres.py

check-snowflake: ## Verify Snowflake transformed data
	@echo "🔍 Checking Snowflake data..."
	docker exec -it ecommerce_dbt python /app/scripts/verify_snowflake.py

##@ 🚀 Pipeline Automation
full-pipeline: ## Run complete data pipeline from start to finish
	@echo "🚀 Running complete data pipeline..."
	$(MAKE) docker-up
	sleep 10
	$(MAKE) setup-postgres
	$(MAKE) seed-data
	$(MAKE) load-snowflake
	$(MAKE) dbt-deps
	$(MAKE) dbt-run
	$(MAKE) dbt-test
	$(MAKE) verify-pipeline
	@echo "🎉 Complete pipeline executed successfully!"

refresh-data: ## Refresh all data (reseed and retransform)
	@echo "🔄 Refreshing all data..."
	$(MAKE) seed-data
	$(MAKE) load-snowflake
	$(MAKE) dbt-run
	$(MAKE) dbt-test
	@echo "✅ Data refresh completed"

##@ 🛠️ Development Tools
lint-sql: ## Lint SQL files (requires sqlfluff)
	@echo "🔍 Linting SQL files..."
	docker exec -it ecommerce_dbt sqlfluff lint dbt_project/models/

format-sql: ## Format SQL files (requires sqlfluff)
	@echo "✨ Formatting SQL files..."
	docker exec -it ecommerce_dbt sqlfluff fix dbt_project/models/

git-setup: ## Setup git hooks and configuration
	@echo "🔧 Setting up git configuration..."
	cp .env.template .env.example
	git add .env.example
	@echo "✅ Git setup completed"

##@ 📊 Monitoring & Logs
show-logs: ## Show recent dbt logs
	@echo "📋 Recent dbt logs:"
	docker exec -it ecommerce_dbt tail -n 50 logs/dbt.log

monitor-runs: ## Monitor dbt run results
	@echo "📊 Monitoring dbt runs..."
	docker exec -it ecommerce_dbt find target/run_results.json -exec cat {} \;

performance-profile: ## Generate dbt performance profile
	@echo "⚡ Generating performance profile..."
	docker exec -it ecommerce_dbt dbt run --vars '{profile_performance: true}'

##@ 🧹 Maintenance
clean-all: ## Clean all artifacts and containers
	@echo "🧹 Cleaning all artifacts..."
	$(MAKE) dbt-clean
	$(MAKE) docker-clean
	@echo "✅ Complete cleanup finished"

backup-db: ## Backup PostgreSQL database
	@echo "💾 Creating database backup..."
	docker exec -i postgres_client pg_dump -h $$POSTGRES_HOST -U $$POSTGRES_USER $$POSTGRES_DB > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created"

health-check: ## Check system health
	@echo "🏥 Checking system health..."
	docker ps
	$(MAKE) dbt-debug
	@echo "✅ Health check completed"

##@ ℹ️ Information
show-env: ## Show environment variables (safe values only)
	@echo "🔧 Environment Configuration:"
	@echo "POSTGRES_HOST: $$POSTGRES_HOST"
	@echo "POSTGRES_DB: $$POSTGRES_DB"
	@echo "POSTGRES_USER: $$POSTGRES_USER"
	@echo "SNOWFLAKE_ACCOUNT: $$SNOWFLAKE_ACCOUNT"
	@echo "SNOWFLAKE_DATABASE: $$SNOWFLAKE_DATABASE"
	@echo "SNOWFLAKE_WAREHOUSE: $$SNOWFLAKE_WAREHOUSE"

show-models: ## List all dbt models
	@echo "📋 dbt Models:"
	docker exec -it ecommerce_dbt dbt list

show-tests: ## List all dbt tests
	@echo "🧪 dbt Tests:"
	docker exec -it ecommerce_dbt dbt list --resource-type test

project-status: ## Show overall project status
	@echo "📊 Project Status:"
	@echo "=================="
	$(MAKE) show-env
	@echo ""
	$(MAKE) show-models
	@echo ""
	$(MAKE) show-tests

##@ Default
.DEFAULT_GOAL := help
