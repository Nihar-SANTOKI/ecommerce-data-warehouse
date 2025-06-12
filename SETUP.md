# Setup Guide

This guide will walk you through setting up the E-commerce Data Warehouse from scratch.

## 📋 Prerequisites

Before starting, ensure you have:

- **Docker & Docker Compose** installed
- **PostgreSQL database** access (AlwaysData, AWS RDS, or local)
- **Snowflake account** with appropriate permissions
- **Git** for version control
- **Python 3.8+** (if running scripts locally)

## 🏗️ Step-by-Step Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/Nihar-SANTOKI/ecommerce-data-warehouse
cd ecommerce-dbt-warehouse

# Create environment file from template
cp .env.template .env

# Edit environment variables
vim .env  # or your preferred editor
```

### 2. Configure Environment Variables

Edit `.env` with your actual database credentials:

```bash
# PostgreSQL (Source Database)
POSTGRES_HOST=your-postgres-host.alwaysdata.net
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_secure_password

# Snowflake (Data Warehouse)
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=ECOMMERCE_DW
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_SCHEMA=PUBLIC
```

### 3. Setup PostgreSQL Database

```bash
# Start Docker services
docker-compose up -d

# Create database schema
docker-compose exec dbt python /scripts/setup_postgres.py

# Verify PostgreSQL connection
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

### 4. Setup Snowflake Database

**Option A: Using Snowflake Web UI**
1. Log into your Snowflake account
2. Open a new worksheet
3. Copy and paste the contents of `scripts/snowflake_setup.sql`
4. Replace `YOUR_USERNAME` with your actual Snowflake username
5. Execute the script

**Option B: Using SnowSQL CLI**
```bash
# If you have SnowSQL installed
snowsql -a your-account.snowflakecomputing.com -u your-username -f scripts/snowflake_setup.sql
```

### 5. Generate Test Data

```bash
# Generate and load test data into PostgreSQL
docker-compose exec dbt python /scripts/seed_data.py

# This will create:
# - 1,000 customers
# - 500 products  
# - 5,000 orders
```

### 6. Load Data to Snowflake

```bash
# Extract from PostgreSQL and load to Snowflake
docker-compose exec dbt python /scripts/loadDataToSnowflake.py

# Verify data was loaded correctly
docker-compose exec dbt python /scripts/check_snowflake.py
```

### 7. Run dbt Transformations

```bash
# Install dbt package dependencies
docker-compose exec dbt dbt deps

# Run all dbt models
docker-compose exec dbt dbt run

# Run data quality tests
docker-compose exec dbt dbt test

# Generate documentation
docker-compose exec dbt dbt docs generate
docker-compose exec dbt dbt docs serve --host 0.0.0.0 --port 8080
```

### 8. Verify Complete Pipeline

```bash
# Run end-to-end verification
docker-compose exec dbt python /scripts/verify_data_flow.py

# This checks:
# - PostgreSQL source data
# - Snowflake staging data
# - dbt transformed models
# - Data quality and consistency
```

## 🎯 Quick Start (Automated)

For a fully automated setup, run these commands in sequence:

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Setup PostgreSQL schema
docker-compose exec dbt python /scripts/setup_postgres.py

# 3. Generate test data
docker-compose exec dbt python /scripts/seed_data.py

# 4. Load data to Snowflake
docker-compose exec dbt python /scripts/loadDataToSnowflake.py

# 5. Run dbt transformations
docker-compose exec dbt dbt deps
docker-compose exec dbt dbt run

# 6. Execute data quality tests
docker-compose exec dbt dbt test

# 7. Verify end-to-end pipeline
docker-compose exec dbt python /scripts/verify_data_flow.py

# 8. Generate documentation
docker-compose exec dbt dbt docs generate
docker-compose exec dbt dbt docs serve --host 0.0.0.0 --port 8080
```

## 🔧 Configuration Details

### PostgreSQL Configuration

The PostgreSQL database should have these tables:
- `customers` - Customer master data
- `products` - Product catalog
- `orders` - Transaction data

Schema is automatically created by `docker-compose exec dbt python /scripts/setup_postgres.py`.

### Snowflake Configuration

Required Snowflake objects:
- **Database**: `ECOMMERCE_DW`
- **Schemas**: `PUBLIC`, `STAGING`, `CORE`, `FINANCE`
- **Warehouse**: `COMPUTE_WH` (X-Small, auto-suspend)
- **Role**: `TRANSFORMER` with appropriate permissions

### dbt Configuration  

The dbt profile is configured to use environment variables:

```yaml
ecommerce_dw:
  target: snowflake
  outputs:
    postgres:
      type: postgres
      host: "{{ env_var('POSTGRES_HOST') }}"
      user: "{{ env_var('POSTGRES_USER') }}"
      password: "{{ env_var('POSTGRES_PASSWORD') }}"
      port: 5432
      dbname: "{{ env_var('POSTGRES_DB') }}"
      schema: public
      threads: 4
      keepalives_idle: 0

    snowflake:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"
      threads: 4
      client_session_keep_alive: False
      query_tag: dbt_ecommerce
```

## 🚨 Troubleshooting

If you encounter issues during setup, check the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) file for detailed solutions to common problems.

## 🧪 Testing Your Setup

### Smoke Tests

```bash
# Test 1: Data exists in PostgreSQL
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM customers;"

# Test 2: Data loaded to Snowflake
docker-compose exec dbt python /scripts/check_snowflake.py

# Test 3: dbt models run successfully
docker-compose exec dbt dbt run

# Test 4: All tests pass
docker-compose exec dbt dbt test

# Test 5: Documentation generates
docker-compose exec dbt dbt docs generate
```

### Verification Queries

Run these queries to verify your setup:

```bash
# Check PostgreSQL source data
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT 
    'customers' as table_name, COUNT(*) as row_count FROM customers
UNION ALL
SELECT 
    'products' as table_name, COUNT(*) as row_count FROM products
UNION ALL
SELECT 
    'orders' as table_name, COUNT(*) as row_count FROM orders;
"

# Check dbt models (run this in Snowflake or via dbt)
docker-compose exec dbt dbt run-operation check_model_counts
```

### Sample Queries

Once setup is complete, you can run these sample queries in Snowflake:

```sql
-- Check customer dimension
SELECT COUNT(*) FROM CORE.DIM_CUSTOMERS;

-- Check monthly revenue
SELECT 
    month_name,
    year,
    total_revenue,
    total_orders 
FROM FINANCE.REVENUE_ANALYSIS 
ORDER BY year DESC, month DESC 
LIMIT 12;

-- Check fact table
SELECT COUNT(*) FROM CORE.FACT_ORDERS;
```

## 🔄 Regular Operations

### Daily Operations
```bash
# Refresh data
docker-compose exec dbt python /scripts/loadDataToSnowflake.py
docker-compose exec dbt dbt run

# Run tests
docker-compose exec dbt dbt test

# Check pipeline health
docker-compose exec dbt python /scripts/verify_data_flow.py
```

### Weekly Operations
```bash
# Full pipeline refresh
docker-compose exec dbt python /scripts/setup_postgres.py
docker-compose exec dbt python /scripts/seed_data.py
docker-compose exec dbt python /scripts/loadDataToSnowflake.py
docker-compose exec dbt dbt run
docker-compose exec dbt dbt test

# Generate fresh documentation
docker-compose exec dbt dbt docs generate
docker-compose exec dbt dbt docs serve --host 0.0.0.0 --port 8080

# Performance check
docker-compose exec dbt dbt run --vars '{"performance_profile": true}'
```

### Monthly Operations
```bash
# Database backup (PostgreSQL)
docker-compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d).sql

# Clean artifacts
docker-compose exec dbt dbt clean
docker system prune -f

# Update dependencies
docker-compose exec dbt dbt deps
```

## 🛠️ Advanced Usage

### Development Mode
```bash
# Start in development mode with volume mounts
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Make changes to models and run
docker-compose exec dbt dbt run --models modified_model

# Hot reload documentation
docker-compose exec dbt dbt docs generate
```

### Production Deployment
```bash
# Use production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run with production settings
docker-compose exec dbt dbt run --target prod
```

### Monitoring and Logs
```bash
# View real-time logs
docker-compose logs -f dbt

# Monitor container resources
docker-compose top

# Check container health
docker-compose ps
```

## 🤝 Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Open a GitHub issue for bugs or feature requests
- Review dbt documentation: https://docs.getdbt.com/
