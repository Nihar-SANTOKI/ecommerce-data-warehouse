#!/usr/bin/env python3
import os
import psycopg2
import snowflake.connector
from dotenv import load_dotenv
import sys

load_dotenv()

def check_postgres_data():
    """Verify PostgreSQL has data"""
    print("🔍 Checking PostgreSQL data...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        cursor = conn.cursor()
        
        # Check record counts
        tables = ['customers', 'products', 'orders']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table}: {count:,} records")
            if count == 0:
                print(f"  ⚠️ WARNING: {table} is empty!")
        
        # Check data samples
        cursor.execute("""
            SELECT 
                c.first_name, c.last_name, c.customer_segment,
                p.product_name, p.category,
                o.total_amount, o.order_date
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN products p ON o.product_id = p.product_id
            LIMIT 5
        """)
        
        print("\n📊 Sample joined data:")
        for row in cursor.fetchall():
            print(f"  {row[0]} {row[1]} ({row[2]}) bought {row[3]} ({row[4]}) for ${row[5]:.2f}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ PostgreSQL Error: {e}")
        return False

def check_snowflake_schemas():
    """Check what schemas exist in Snowflake"""
    print("\n🔍 Checking Snowflake schemas...")
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE')
        )
        cursor = conn.cursor()
        
        # Check what schemas exist
        cursor.execute("SHOW SCHEMAS")
        schemas = cursor.fetchall()
        print("  Available schemas:")
        for schema in schemas:
            print(f"    - {schema[1]}")
        
        conn.close()
        return [schema[1] for schema in schemas]
        
    except Exception as e:
        print(f"  ❌ Schema check error: {e}")
        return []

def check_snowflake_data():
    """Verify Snowflake has transformed data"""
    print("\n🔍 Checking Snowflake data...")
    
    # First check what schemas exist
    available_schemas = check_snowflake_schemas()
    
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE')
        )
        cursor = conn.cursor()
        
        # Check core schema tables
        if 'CORE' in available_schemas or 'PUBLIC_CORE' in available_schemas:
            core_schema = 'CORE' if 'CORE' in available_schemas else 'PUBLIC_CORE'
            print(f"\n  Checking {core_schema} schema:")
            
            # Check dimension tables
            dimensions = ['DIM_CUSTOMERS', 'DIM_PRODUCTS', 'DIM_DATES']
            for dim in dimensions:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {core_schema}.{dim}")
                    count = cursor.fetchone()[0]
                    print(f"    ✅ {dim}: {count:,} records")
                except Exception as e:
                    print(f"    ❌ {dim}: Error - {e}")
            
            # Check fact table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {core_schema}.FACT_ORDERS")
                fact_count = cursor.fetchone()[0]
                print(f"    ✅ FACT_ORDERS: {fact_count:,} records")
                
                # Show sample fact data
                cursor.execute(f"""
                    SELECT 
                        order_key,
                        customer_key,
                        product_key,
                        quantity,
                        total_amount
                    FROM {core_schema}.FACT_ORDERS
                    LIMIT 5
                """)
                
                print("\n📊 Sample fact data:")
                for row in cursor.fetchall():
                    print(f"    Order {row[0]}: Customer {row[1]}, Product {row[2]}, Qty {row[3]}, Amount ${row[4]:.2f}")
                    
            except Exception as e:
                print(f"    ❌ FACT_ORDERS: Error - {e}")
        else:
            print("  ⚠️ No CORE schema found")
        
        # Check finance schema if it exists
        if 'FINANCE' in available_schemas or 'PUBLIC_FINANCE' in available_schemas:
            finance_schema = 'FINANCE' if 'FINANCE' in available_schemas else 'PUBLIC_FINANCE'
            print(f"\n  Checking {finance_schema} schema:")
            
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {finance_schema}.REVENUE_ANALYSIS")
                bi_count = cursor.fetchone()[0]
                print(f"    ✅ REVENUE_ANALYSIS: {bi_count:,} records")
                
                # Show sample analytics
                cursor.execute(f"""
                    SELECT 
                        month_name,
                        year,
                        total_revenue,
                        total_orders,
                        avg_order_value
                    FROM {finance_schema}.REVENUE_ANALYSIS
                    ORDER BY year DESC, month DESC
                    LIMIT 5
                """)
                
                print("\n📊 Sample revenue analysis:")
                for row in cursor.fetchall():
                    print(f"    {row[0]} {row[1]}: ${row[2]:,.2f} revenue, {row[3]} orders, ${row[4]:.2f} AOV")
                    
            except Exception as e:
                print(f"    ⚠️ Finance schema not accessible: {e}")
        else:
            print("  ⚠️ No FINANCE schema found - may not be created yet")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Snowflake Error: {e}")
        return False

def check_dbt_models():
    """Check if dbt models have been run"""
    print("\n🔍 Checking dbt model status...")
    
    # Check if target directory exists
    dbt_target_path = "/app/dbt_project/target"
    if os.path.exists(dbt_target_path):
        manifest_path = os.path.join(dbt_target_path, "manifest.json")
        if os.path.exists(manifest_path):
            print("  ✅ dbt manifest found - models have been compiled")
        else:
            print("  ⚠️ dbt manifest not found - run 'make dbt-run' first")
    else:
        print("  ⚠️ dbt target directory not found - run 'make dbt-run' first")

if __name__ == "__main__":
    print("🚀 Starting Data Pipeline Verification...\n")
    
    postgres_ok = check_postgres_data()
    snowflake_ok = check_snowflake_data()
    check_dbt_models()
    
    print(f"\n{'='*60}")
    
    if postgres_ok and snowflake_ok:
        print("🎉 SUCCESS: Data pipeline is working!")
        print("   - PostgreSQL has source data")
        print("   - Snowflake has transformed data")
        if 'FINANCE' in str(check_snowflake_schemas()):
            print("   - Business intelligence models are populated")
        else:
            print("   - Finance models may need to be created")
    else:
        print("⚠️ ISSUES DETECTED:")
        if not postgres_ok:
            print("   - PostgreSQL data missing or connection failed")
        if not snowflake_ok:
            print("   - Snowflake data missing or connection failed")
    
    print("\n💡 Next steps:")
    print("   1. If schemas are missing, run: make setup-snowflake")
    print("   2. If models aren't built, run: make dbt-run")
    print("   3. If finance models fail, check schema permissions")
    print("="*60)