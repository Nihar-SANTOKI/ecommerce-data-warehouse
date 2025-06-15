import requests
import json
import time

def check_stream_health():
    # Check Spark UI
    spark_ui = requests.get("http://spark:4040/api/v1/applications")
    if spark_ui.status_code != 200:
        send_alert("Spark UI unavailable")
    
    # Check Kafka consumer lag
    kafka_lag = get_consumer_lag()
    if kafka_lag > 1000:
        send_alert(f"High Kafka consumer lag: {kafka_lag}")

def send_alert(message):
    # Send to Redis for dashboard
    redis.rpush("alerts", json.dumps({
        "timestamp": int(time.time()),
        "severity": "high",
        "message": message
    }))
    # Send to Kafka for processing
    producer.send("system_alerts", {"alert": message})

if __name__ == "__main__":
    while True:
        check_stream_health()
        time.sleep(60)