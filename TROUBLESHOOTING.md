# TROUBLESHOOTING GUIDE

This guide helps resolve common issues encountered when working with the E-commerce Data Warehouse project.

## 🚨 Common Issues & Solutions

### 1. Database Connection Issues

#### PostgreSQL Connection Errors

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check if PostgreSQL service is running
docker ps | grep postgres

# Verify environment variables
cat .env | grep POSTGRES

# Test connection manually
docker exec -it postgres_client psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB

# If using AlwaysData, ensure:
# - Host format: postgresql-XXXXX.alwaysdata.net
# - Port is correct (usually 5432)
# - Database name matches your AlwaysData database
```

#### Snowflake Connection Errors

**Problem**: `snowflake.connector.errors.DatabaseError: Failed to connect`

**Solutions**:
```bash
# Verify Snowflake credentials
echo "Account: $SNOWFLAKE_ACCOUNT"
echo "User: $SNOWFLAKE_USER"
echo "Database: $SNOWFLAKE_DATABASE"

# Common issues:
# 1. Account identifier format: Should be XXXXX-XXXXX (without .snowflakecomputing.com)
# 2. Case sensitivity: User names are case-sensitive in Snowflake
# 3. Password special characters: Escape special characters in .env file

# Test connection with Python
python3 -c "
import snowflake.connector
import os
from dotenv import load_dotenv
load_dotenv()
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD')
)
print('✅ Snowflake connection successful')
conn.close()
"
```

### 2. Docker & Environment Issues

#### Container Won't Start

**Problem**: `docker-compose up` fails or containers exit immediately

**Solutions**:
```bash
# Check Docker daemon is running
docker --version
docker ps

# Rebuild containers if needed
docker-compose down --volumes
docker-compose build --no-cache
docker-compose up -d

# Check container logs
docker-compose logs dbt
docker-compose logs postgres-client

# Verify .env file exists and has correct permissions
ls -la .env
chmod 600 .env
```

#### Environment Variables Not Loading

**Problem**: Variables from `.env` file not available in containers

**Solutions**:
```bash
# Ensure .env file is in project root
cat .env

# Check if variables are loaded in container
docker exec -it ecommerce_dbt env | grep POSTGRES
docker exec -it ecommerce_dbt env | grep SNOWFLAKE

# If missing, restart containers
docker-compose down
docker-compose up -d
```

### 3. Data Loading Issues

#### No Data in PostgreSQL

**Problem**: `seed_data.py` runs but no data appears

**Solutions**:
```bash
# Check if tables exist
docker exec -it postgres_client psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

# Verify data was inserted
docker exec -it postgres_client psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT COUNT(*) FROM customers;"

# If tables don't exist, run setup first
python scripts/setup_postgres.sql

# Check for errors in seed script
python scripts/seed_data.py 2>&1 | tee seed_errors.log
```

#### Snowflake Load Failures

**Problem**: `loadDataToSnowflake.py` fails with permission errors

**Solutions**:
```bash
# Check Snowflake permissions
# Connect to Snowflake console and run:
USE ROLE SYSADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE TRANSFORMER;
GRANT CREATE TABLE ON SCHEMA PUBLIC TO ROLE TRANSFORMER;
GRANT CREATE VIEW ON SCHEMA PUBLIC TO ROLE TRANSFORMER;

# Verify warehouse is running
USE WAREHOUSE COMPUTE_WH;
SELECT CURRENT_WAREHOUSE();

# Check if data exists in staging
SELECT COUNT(*) FROM CUSTOMERS;
SELECT COUNT(*) FROM PRODUCTS;
SELECT COUNT(*) FROM ORDERS;
```

### 4. dbt Transformation Issues

#### dbt Models Fail to Run

**Problem**: `dbt run` fails with compilation or execution errors

**Solutions**:
```bash
# Check dbt installation and version
docker exec -it ecommerce_dbt dbt --version

# Verify dbt can connect to Snowflake
docker exec -it ecommerce_dbt dbt debug --project-dir /app/dbt_project

# Install dbt packages if missing
docker exec -it ecommerce_dbt dbt deps --project-dir /app/dbt_project

# Run with verbose logging
docker exec -it ecommerce_dbt dbt run --project-dir /app/dbt_project --profiles-dir /root/.dbt --debug

# Check specific model
docker exec -it ecommerce_dbt dbt run --project-dir /app/dbt_project --profiles-dir /root/.dbt --select stg_customers
```

#### dbt_utils Package Issues

**Problem**: `dbt_utils.generate_surrogate_key` not found

**Solutions**:
```bash
# Install dbt packages
docker exec -it ecommerce_dbt dbt deps --project-dir /app/dbt_project

# Check packages.yml is correct
cat dbt_project/packages.yml

# If still failing, manually specify version
# In packages.yml:
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
```

#### Schema Not Found Errors

**Problem**: `Object 'SCHEMA.TABLE' does not exist`

**Solutions**:
```bash
# Check if schemas exist in Snowflake
USE DATABASE ECOMMERCE_DW;
SHOW SCHEMAS;

# Create schemas if missing
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS CORE;
CREATE SCHEMA IF NOT EXISTS FINANCE;

# Verify dbt_project.yml schema configuration
cat dbt_project/dbt_project.yml | grep -A 10 models:
```

### 5. Data Quality Issues

#### Missing Date Matches in fact_orders

**Problem**: `missing_date_flag = 1` in fact table

**Solutions**:
```sql
-- Check date range in source data
SELECT MIN(order_date), MAX(order_date) FROM orders;

-- Verify dim_dates covers the range
SELECT MIN(full_date), MAX(full_date) FROM core.dim_dates;

-- Find problematic dates
SELECT DISTINCT order_date 
FROM staging.orders 
WHERE order_date NOT IN (SELECT full_date FROM core.dim_dates);

-- Extend date dimension if needed
-- Update dim_dates.sql with broader date range
```

#### Surrogate Key Collisions

**Problem**: Duplicate surrogate keys in dimension tables

**Solutions**:
```sql
-- Check for duplicates
SELECT customer_key, COUNT(*) 
FROM core.dim_customers 
GROUP BY customer_key 
HAVING COUNT(*) > 1;

-- Verify source data uniqueness
SELECT customer_id, COUNT(*) 
FROM staging.customers 
GROUP BY customer_id 
HAVING COUNT(*) > 1;

-- If source has duplicates, add deduplication logic
```

### 6. Performance Issues

#### Slow dbt Runs

**Problem**: dbt transformations take too long

**Solutions**:
```bash
# Use smaller Snowflake warehouse for development
# In profiles.yml, change warehouse to X-SMALL

# Run specific models only
docker exec -it ecommerce_dbt dbt run --project-dir /app/dbt_project --select staging

# Use incremental models for large fact tables
# Add to fact_orders.sql:
{{ config(
    materialized='incremental',
    unique_key='order_key'
) }}
```

#### High Snowflake Costs

**Problem**: Unexpected Snowflake compute charges

**Solutions**:
```sql
-- Check warehouse usage
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY 
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- Set auto-suspend to 1 minute for development
ALTER WAREHOUSE COMPUTE_WH SET AUTO_SUSPEND = 60;

-- Use X-SMALL warehouse for development
ALTER WAREHOUSE COMPUTE_WH SET WAREHOUSE_SIZE = 'X-SMALL';
```

### 7. Testing & Validation Issues

#### dbt Tests Failing

**Problem**: `dbt test` reports failures

**Solutions**:
```bash
# Run tests with details
docker exec -it ecommerce_dbt dbt test --project-dir /app/dbt_project --profiles-dir /root/.dbt --store-failures

# Check specific test
docker exec -it ecommerce_dbt dbt test --project-dir /app/dbt_project --profiles-dir /root/.dbt --select unique_dim_customers_customer_key

# View failed test results
SELECT * FROM dbt_test_failures.unique_dim_customers_customer_key;
```

## 🔧 Debugging Commands

### Essential Debug Commands

```bash
# 1. Check all container status
docker-compose ps

# 2. View real-time logs
docker-compose logs -f dbt

# 3. Connect to dbt container
docker exec -it ecommerce_dbt bash

# 4. Test database connections
python scripts/verify_data_flow.py

# 5. dbt debug (comprehensive connection test)
docker exec -it ecommerce_dbt dbt debug --project-dir /app/dbt_project --profiles-dir /root/.dbt

# 6. Check dbt compilation
docker exec -it ecommerce_dbt dbt compile --project-dir /app/dbt_project --profiles-dir /root/.dbt
```

### SQL Debugging Queries

```sql
-- Check source data counts
SELECT 'customers' as table_name, COUNT(*) as record_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products  
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;

-- Verify staging layer
SELECT 'stg_customers' as table_name, COUNT(*) as record_count FROM staging.stg_customers
UNION ALL
SELECT 'stg_products', COUNT(*) FROM staging.stg_products
UNION ALL  
SELECT 'stg_orders', COUNT(*) FROM staging.stg_orders;

-- Check dimension integrity
SELECT 
    f.customer_key,
    COUNT(*) as fact_records,
    MAX(CASE WHEN d.customer_key IS NULL THEN 1 ELSE 0 END) as missing_dim
FROM core.fact_orders f
LEFT JOIN core.dim_customers d ON f.customer_key = d.customer_key
GROUP BY f.customer_key
HAVING missing_dim = 1;
```

## 🆘 Getting Help

### Log Collection

When reporting issues, collect these logs:

```bash
# 1. Container logs
docker-compose logs > docker_logs.txt

# 2. dbt logs  
docker exec -it ecommerce_dbt cat /app/dbt_project/logs/dbt.log > dbt_logs.txt

# 3. Environment info
docker exec -it ecommerce_dbt env > container_env.txt

# 4. dbt debug output
docker exec -it ecommerce_dbt dbt debug --project-dir /app/dbt_project --profiles-dir /root/.dbt > dbt_debug.txt
```

### Common Error Patterns

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `Connection refused` | Service not running | Check docker-compose ps |
| `Permission denied` | Insufficient privileges | Check database roles/grants |
| `Object does not exist` | Schema/table missing | Run setup scripts first |
| `Compilation Error` | SQL syntax issue | Check model SQL syntax |
| `Surrogate key collision` | Duplicate source data | Add deduplication logic |
| `Date parsing error` | Invalid date format | Check date format consistency |

### Environment Checklist

Before reporting issues, verify:

- [ ] `.env` file exists with all required variables
- [ ] Docker containers are running (`docker-compose ps`)
- [ ] PostgreSQL has data (`SELECT COUNT(*) FROM customers`)
- [ ] Snowflake connection works (`dbt debug`)
- [ ] dbt packages are installed (`dbt deps`)
- [ ] Schemas exist in Snowflake (`SHOW SCHEMAS`)

---

## 📞 Support Resources

- **Project Issues**: Check GitHub issues for similar problems
- **dbt Documentation**: https://docs.getdbt.com/
- **Snowflake Documentation**: https://docs.snowflake.com/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

Remember: Most issues are environment-related. Start with connection testing and work your way up through the data pipeline.
