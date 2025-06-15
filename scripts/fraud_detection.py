from pyspark.ml import PipelineModel
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

# Load pre-trained fraud detection model
fraud_model = PipelineModel.load("models/fraud_detection_model")

# Define features for fraud detection
def extract_features(order_df):
    return order_df.select(
        col("order_amount"),
        col("quantity"),
        col("discount_amount"),
        (col("order_amount") / col("quantity")).alias("avg_item_price"),
        col("metadata.customer_historical_order_count").cast(IntegerType()).alias("order_count"),
        col("metadata.customer_account_age_days").cast(IntegerType()).alias("account_age")
    )

# Predict fraud probability
def predict_fraud(orders):
    features = extract_features(orders)
    predictions = fraud_model.transform(features)
    return predictions.withColumn("fraud_probability", col("probability")[1])

# UDF to trigger alerts
@udf(BooleanType())
def trigger_alert(fraud_probability):
    return fraud_probability > 0.85

# Add to stream processing
fraud_predictions = predict_fraud(orders)
fraud_alerts = fraud_predictions.filter(trigger_alert(col("fraud_probability")))