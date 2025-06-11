#!/usr/bin/env python3
"""
PostgreSQL to Snowflake Data Loader
Extracts data from PostgreSQL and loads it into Snowflake staging tables
"""

import os
import sys
import pandas as pd
import psycopg2
import snowflake.connector
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging
from snowflake.connector.pandas_tools import write_pandas  # Add to top imports

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PostgreSQLToSnowflakeLoader:
    def __init__(self):
        self.pg_conn = None
        self.sf_conn = None
        self.setup_connections()
    
    def setup_connections(self):
        """Setup database connections"""
        try:
            # PostgreSQL connection
            self.pg_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT', 5432),
                database=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            logger.info("✓ PostgreSQL connection established")
            
            # Snowflake connection
            self.sf_conn = snowflake.connector.connect(
                account=os.getenv('SNOWFLAKE_ACCOUNT'),
                user=os.getenv('SNOWFLAKE_USER'),
                password=os.getenv('SNOWFLAKE_PASSWORD'),
                warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
                database=os.getenv('SNOWFLAKE_DATABASE'),
                schema='PUBLIC'
            )
            logger.info("✓ Snowflake connection established")
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            sys.exit(1)
    
    def extract_table_data(self, table_name):
        """Extract data from PostgreSQL table"""
        try:
            logger.info(f"Extracting data from {table_name}...")
            
            # Create SQLAlchemy engine for pandas
            engine = create_engine(
                f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
                f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DB')}"
            )
            
            # Read data into pandas DataFrame
            df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
            logger.info(f"✓ Extracted {len(df)} records from {table_name}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting {table_name}: {e}")
            return None
    
    def create_staging_table(self, table_name, df):
        """Create staging table in Snowflake"""
        cursor = self.sf_conn.cursor()
        
        # Drop table if exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table based on DataFrame structure
        if table_name == 'CUSTOMERS':
            create_sql = """
            CREATE TABLE CUSTOMERS (
                CUSTOMER_ID INTEGER,
                FIRST_NAME VARCHAR(50),
                LAST_NAME VARCHAR(50),
                EMAIL VARCHAR(100),
                PHONE VARCHAR(20),
                ADDRESS_LINE_1 VARCHAR(100),
                ADDRESS_LINE_2 VARCHAR(100),
                CITY VARCHAR(50),
                STATE VARCHAR(50),
                COUNTRY VARCHAR(50),
                POSTAL_CODE VARCHAR(20),
                REGISTRATION_DATE DATE,
                CUSTOMER_SEGMENT VARCHAR(20),
                IS_ACTIVE BOOLEAN,
                CREATED_AT TIMESTAMP,
                UPDATED_AT TIMESTAMP
            )
            """
        elif table_name == 'PRODUCTS':
            create_sql = """
            CREATE TABLE PRODUCTS (
                PRODUCT_ID INTEGER,
                PRODUCT_NAME VARCHAR(200),
                CATEGORY VARCHAR(50),
                SUBCATEGORY VARCHAR(50),
                BRAND VARCHAR(50),
                SUPPLIER VARCHAR(100),
                UNIT_PRICE DECIMAL(10,2),
                COST_PRICE DECIMAL(10,2),
                DESCRIPTION TEXT,
                IS_ACTIVE BOOLEAN,
                CREATED_AT TIMESTAMP,
                UPDATED_AT TIMESTAMP
            )
            """
        elif table_name == 'ORDERS':
            create_sql = """
            CREATE TABLE ORDERS (
                ORDER_ID INTEGER,
                CUSTOMER_ID INTEGER,
                PRODUCT_ID INTEGER,
                ORDER_DATE TIMESTAMP,
                QUANTITY INTEGER,
                UNIT_PRICE DECIMAL(10,2),
                DISCOUNT_AMOUNT DECIMAL(10,2),
                TAX_AMOUNT DECIMAL(10,2),
                TOTAL_AMOUNT DECIMAL(10,2),
                ORDER_STATUS VARCHAR(20),
                PAYMENT_METHOD VARCHAR(20),
                SHIPPING_ADDRESS TEXT,
                CREATED_AT TIMESTAMP,
                UPDATED_AT TIMESTAMP
            )
            """
        
        cursor.execute(create_sql)
        logger.info(f"✓ Created staging table {table_name}")
        cursor.close()
    

    def load_to_snowflake(self, table_name, df):
        """Load DataFrame to Snowflake staging table"""
        try:
            # Ensure column names are uppercase to match Snowflake schema
            df.columns = [col.upper() for col in df.columns]

            # Create staging table
            self.create_staging_table(table_name, df)
            
            # Use write_pandas for efficient, type-safe loading
            success, nchunks, nrows, _ = write_pandas(
                conn=self.sf_conn,
                df=df,
                table_name=table_name,
                schema='PUBLIC',
                database=os.getenv('SNOWFLAKE_DATABASE'),
                auto_create_table=False,
                overwrite=False
            )
            
            if success:
                logger.info(f"✓ Loaded {nrows} records into Snowflake {table_name}")
            else:
                raise Exception("write_pandas reported failure")
                
        except Exception as e:
            logger.error(f"Error loading {table_name} to Snowflake: {e}")
            raise

    
    def verify_data_load(self):
        """Verify data was loaded correctly"""
        cursor = self.sf_conn.cursor()
        
        tables = ['CUSTOMERS', 'PRODUCTS', 'ORDERS']
        
        logger.info("\n" + "="*50)
        logger.info("DATA LOAD VERIFICATION")
        logger.info("="*50)
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"{table}: {count:,} records")
        
        # Show sample data
        cursor.execute("""
            SELECT 
                CAST(c.FIRST_NAME AS STRING), 
                CAST(c.LAST_NAME AS STRING), 
                CAST(c.CUSTOMER_SEGMENT AS STRING),
                CAST(p.PRODUCT_NAME AS STRING), 
                CAST(p.CATEGORY AS STRING),
                CAST(o.TOTAL_AMOUNT AS STRING), 
                CAST(o.ORDER_DATE AS STRING)
            FROM ORDERS o
            JOIN CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
            JOIN PRODUCTS p ON o.PRODUCT_ID = p.PRODUCT_ID
            LIMIT 5
        """)

        
        logger.info("\nSample joined data:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]} {row[1]} ({row[2]}) bought {row[3]} ({row[4]}) for ${row[5]} on {row[6]}")
        
        cursor.close()
        logger.info("="*50)
    
    def run_full_load(self):
        """Run complete data load process"""
        tables = ['customers', 'products', 'orders']
        
        logger.info("Starting PostgreSQL to Snowflake data load...")
        
        for table in tables:
            try:
                # Extract from PostgreSQL
                df = self.extract_table_data(table)
                if df is not None:
                    # Load to Snowflake
                    self.load_to_snowflake(table.upper(), df)
                else:
                    logger.error(f"Failed to extract {table}")
                    
            except Exception as e:
                logger.error(f"Failed to load {table}: {e}")
                raise
        
        # Verify the load
        self.verify_data_load()
        
        logger.info("✓ Data load completed successfully!")
    
    def close_connections(self):
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.sf_conn:
            self.sf_conn.close()
        logger.info("✓ Connections closed")

def main():
    loader = PostgreSQLToSnowflakeLoader()
    
    try:
        loader.run_full_load()
    except Exception as e:
        logger.error(f"Data load failed: {e}")
        sys.exit(1)
    finally:
        loader.close_connections()

if __name__ == "__main__":
    main()