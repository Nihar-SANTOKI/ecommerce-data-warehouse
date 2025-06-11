# Setup Guide

This guide will walk you through setting up the E-commerce Data Warehouse from scratch.

## 📋 Prerequisites

Before starting, ensure you have:

- **Docker & Docker Compose** installed
- **PostgreSQL database** access (AlwaysData, AWS RDS, or local)
- **Snowflake account** with appropriate permissions
- **Git** for version control
- **Python 3.11+** (if running scripts locally)

## 🏗️ Step-by-Step Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <your-repo-url>
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
make docker-up

# Create database schema
make setup-postgres

# Verify PostgreSQL connection
make check-postgres
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
make seed-data

# This will create:
# - 1,000 customers
# - 500 products  
# - 5,000 orders
```

### 6. Load Data to Snowflake

```bash
# Extract from PostgreSQL and load to Snowflake
make load-snowflake

# Verify data was loaded correctly
make check-snowflake
```

### 7. Run dbt Transformations

```bash
# Install dbt package dependencies
make dbt-deps

# Run all dbt models
make dbt-run

# Run data quality tests
make dbt-test

# Generate documentation
make dbt-docs
```

### 8. Verify Complete Pipeline

```bash
# Run end-to-end verification
make verify-pipeline

# This checks:
# - PostgreSQL source data
# - Snowflake staging data
# - dbt transformed models
# - Data quality and consistency
```

## 🎯 Quick Start (Automated)

For a fully automated setup:

```bash
# Run complete pipeline from scratch
make full-pipeline

# This will:
# 1. Start Docker services
# 2. Setup PostgreSQL schema
# 3. Generate test data
# 4. Load data to Snowflake
# 5. Run dbt transformations
# 6. Execute data quality tests
# 7. Verify end-to-end pipeline
```

## 🔧 Configuration Details

### PostgreSQL Configuration

The PostgreSQL database should have these tables:
- `customers` - Customer master data
- `products` - Product catalog
- `orders` - Transaction data

Schema is automatically created by `make setup-postgres`.

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

### Common Issues

**Docker Services Won't Start**
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check port conflicts
docker ps -a
netstat -tuln | grep 5432
```

**PostgreSQL Connection Failed**
```bash
# Test connection manually
docker exec -it postgres_client psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"

# Check environment variables
make show-env
```

**Snowflake Connection Issues**
```bash
# Debug dbt connection
make dbt-debug

# Check Snowflake account details
# Ensure account URL is correct: account.region.snowflakecomputing.com
```

**dbt Models Fail to Run**
```bash
# Check specific model
docker exec -it ecommerce_dbt dbt run --models stg_customers

# View detailed logs
docker exec -it ecommerce_dbt dbt --debug run --models stg_customers

# Check data exists in source
make check-snowflake
```

**Missing Data in Snowflake**
```bash
# Verify data load
make verify-pipeline

# Reload data
make load-snowflake

# Check source data
make check-postgres
```

### Getting Help

1. **Check logs**: `make docker-logs`
2. **Debug dbt**: `make dbt-debug`
3. **Verify data**: `make verify-pipeline`
4. **Show environment**: `make show-env`
5. **Health check**: `make health-check`

## 🧪 Testing Your Setup

### Smoke Tests

```bash
# Test 1: Data exists in PostgreSQL
make check-postgres

# Test 2: Data loaded to Snowflake
make check-snowflake

# Test 3: dbt models run successfully
make dbt-run

# Test 4: All tests pass
make dbt-test

# Test 5: Documentation generates
make dbt-docs
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
make refresh-data

# Run tests
make dbt-test

# Check pipeline health
make health-check
```

### Weekly Operations
```bash
# Full pipeline refresh
make full-pipeline

# Generate fresh documentation
make dbt-docs

# Performance check
make performance-profile
```

### Monthly Operations
```bash
# Database backup
make backup-db

# Clean artifacts
make clean-all

# Update dependencies
make dbt-deps
```

## 📚 Next Steps

After successful setup:

1. **Explore the data**: Use `make dbt-docs` to browse the data lineage
2. **Add new models**: Create custom analytics in `dbt_project/models/marts/`
3. **Connect BI tools**: Point Tableau/PowerBI to the Snowflake `CORE` schema
4. **Add more sources**: Extend the pipeline with additional data sources
5. **Schedule runs**: Set up Airflow or dbt Cloud for production scheduling

## 🤝 Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Open a GitHub issue for bugs or feature requests
- Review dbt documentation: https://docs.getdbt.com/
