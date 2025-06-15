from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import os

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("EcommerceStreamProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0") \
    .getOrCreate()

# Define schemas for Kafka topics
order_schema = StructType([
    StructField("order_id", IntegerType()),
    StructField("customer_id", IntegerType()),
    StructField("product_id", IntegerType()),
    StructField("event_type", StringType()),
    StructField("order_amount", DoubleType()),
    StructField("quantity", IntegerType()),
    StructField("discount_amount", DoubleType()),
    StructField("tax_amount", DoubleType()),
    StructField("order_status", StringType()),
    StructField("payment_method", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("metadata", MapType(StringType(), StringType()))
])

inventory_schema = StructType([
    StructField("product_id", IntegerType()),
    StructField("event_type", StringType()),
    StructField("current_stock", IntegerType()),
    StructField("previous_stock", IntegerType()),
    StructField("reorder_point", IntegerType()),
    StructField("cost_per_unit", DoubleType()),
    StructField("timestamp", TimestampType()),
    StructField("metadata", MapType(StringType(), StringType()))
])

# Kafka Configuration
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

def process_order_stream():
    """Process order events stream"""
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "orders") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parse JSON and apply schema
    orders = df.select(
        from_json(col("value").cast("string"), order_schema).alias("data")
        .select("data.*")
    
    # Fraud detection logic
    fraud_orders = orders.filter(
        (col("order_amount") > 1000) & 
        (col("payment_method") == "CREDIT_CARD") &
        (col("metadata.customer_new") == "true")
    )
    
    # Write fraud alerts to console
    fraud_query = fraud_orders.writeStream \
        .outputMode("append") \
        .format("console") \
        .start()
    
    return fraud_query

def process_inventory_stream():
    """Process inventory events stream"""
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "inventory") \
        .option("startingOffsets", "latest") \
        .load()
    
    inventory = df.select(
        from_json(col("value").cast("string"), inventory_schema).alias("data")
        .select("data.*")
    
    # Low stock alerts
    low_stock = inventory.filter(
        col("current_stock") < col("reorder_point")
    )
    
    # Write to Redis for real-time dashboard
    redis_query = low_stock.writeStream \
        .outputMode("append") \
        .format("org.apache.spark.sql.redis") \
        .option("table", "low_stock_alerts") \
        .option("key.column", "product_id") \
        .option("host", "redis") \
        .option("port", "6379") \
        .start()
    
    return redis_query

def process_revenue_stream():
    """Calculate real-time revenue metrics"""
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "orders") \
        .option("startingOffsets", "latest") \
        .load()
    
    orders = df.select(
        from_json(col("value").cast("string"), order_schema).alias("data")
        .select("data.*")
    
    # Revenue per minute
    revenue = orders.withWatermark("timestamp", "1 minute") \
        .groupBy(window(col("timestamp"), "1 minute")) \
        .agg(
            sum("order_amount").alias("total_revenue"),
            count("*").alias("order_count"),
            approx_count_distinct("customer_id").alias("unique_customers")
        )
    
    # Write to PostgreSQL
    def write_to_postgres(batch_df, batch_id):
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/ecommerce") \
            .option("dbtable", "real_time_revenue") \
            .option("user", os.getenv("POSTGRES_USER")) \
            .option("password", os.getenv("POSTGRES_PASSWORD")) \
            .mode("append") \
            .save()
    
    revenue_query = revenue.writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("complete") \
        .start()
    
    return revenue_query

if __name__ == "__main__":
    queries = [
        process_order_stream(),
        process_inventory_stream(),
        process_revenue_stream()
    ]
    
    for query in queries:
        query.awaitTermination()