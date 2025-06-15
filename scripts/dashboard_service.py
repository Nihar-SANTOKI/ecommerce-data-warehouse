from flask import Flask, render_template
from flask_sse import sse
import redis
import json
import os

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://redis:6379"
app.register_blueprint(sse, url_prefix='/stream')

r = redis.Redis(host='redis', port=6379, db=0)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/metrics')
def get_metrics():
    # Get real-time metrics from Redis
    revenue = r.get('current_revenue') or 0
    orders = r.get('orders_last_min') or 0
    low_stock = r.len('low_stock_alerts') or 0
    
    return json.dumps({
        'revenue': float(revenue),
        'orders': int(orders),
        'low_stock_alerts': low_stock
    })

@app.route('/alerts')
def get_alerts():
    alerts = []
    for key in r.scan_iter("alert:*"):
        alert_data = json.loads(r.get(key))
        alerts.append(alert_data)
    
    return json.dumps(alerts[:10])  # Return latest 10 alerts

def event_listener():
    pubsub = r.pubsub()
    pubsub.subscribe('revenue_updates', 'fraud_alerts')
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            sse.publish({
                'type': message['channel'].decode(),
                'data': message['data'].decode()
            }, type='event')

if __name__ == '__main__':
    import threading
    threading.Thread(target=event_listener, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)