"""
Event Producer System for E-commerce Real-time Data Platform
Monitors PostgreSQL for changes and produces events to Kafka
"""

import json
import logging
import time
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os
from dataclasses import dataclass, asdict
import threading
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OrderEvent:
    order_id: int
    customer_id: int
    product_id: int
    event_type: str  # 'created', 'updated', 'cancelled', 'shipped', 'delivered'
    order_amount: float
    quantity: int
    discount_amount: float
    tax_amount: float
    order_status: str
    payment_method: str
    timestamp: str
    metadata: Dict[str, Any] = None

@dataclass
class InventoryEvent:
    product_id: int
    event_type: str  # 'stock_change', 'restock', 'low_stock_alert'
    current_stock: int
    previous_stock: int
    reorder_point: int
    cost_per_unit: float
    timestamp: str
    metadata: Dict[str, Any] = None

@dataclass
class PriceEvent:
    product_id: int
    event_type: str  # 'price_change', 'discount_applied', 'promotion_start'
    old_price: float
    new_price: float
    discount_percentage: float
    effective_date: str
    timestamp: str
    metadata: Dict[str, Any] = None

@dataclass
class CustomerEvent:
    customer_id: int
    event_type: str  # 'registration', 'login', 'cart_action', 'profile_update'
    customer_segment: str
    action_details: Dict[str, Any]
    timestamp: str
    metadata: Dict[str, Any] = None

class EventProducer:
    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            retry_backoff_ms=100,
            request_timeout_ms=30000,
            max_in_flight_requests_per_connection=1
        )
        
        # Track last processed timestamps
        self.last_processed = {
            'orders': None,
            'products': None,  
            'customers': None
        }
        
        # Running flag for graceful shutdown
        self.running = True
        
        logger.info("Event Producer initialized")

    def get_db_connection(self):
        """Get PostgreSQL database connection"""
        try:
            return psycopg2.connect(**self.postgres_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def send_event(self, topic: str, event_data: Dict[str, Any]):
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(topic, value=event_data)
            future.get(timeout=10)  # Wait for send to complete
            logger.info(f"Event sent to {topic}: {event_data.get('event_type', 'unknown')}")
        except KafkaError as e:
            logger.error(f"Failed to send event to {topic}: {e}")
            raise

    def monitor_orders(self):
        """Monitor orders table for changes"""
        logger.info("Starting order monitoring...")
        
        while self.running:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Get new/updated orders
                where_clause = ""
                if self.last_processed['orders']:
                    where_clause = f"WHERE updated_at > '{self.last_processed['orders']}'"
                
                query = f"""
                SELECT 
                    order_id, customer_id, product_id, order_date,
                    quantity, unit_price, discount_amount, tax_amount,
                    total_amount, order_status, payment_method,
                    created_at, updated_at
                FROM orders 
                {where_clause}
                ORDER BY updated_at ASC
                LIMIT 100
                """
                
                cursor.execute(query)
                orders = cursor.fetchall()
                
                for order in orders:
                    # Determine event type based on order status and timing
                    event_type = self._determine_order_event_type(order)
                    
                    order_event = OrderEvent(
                        order_id=order[0],
                        customer_id=order[1],
                        product_id=order[2],
                        event_type=event_type,
                        order_amount=float(order[8]),
                        quantity=order[4],
                        discount_amount=float(order[6]),
                        tax_amount=float(order[7]),
                        order_status=order[9],
                        payment_method=order[10],
                        timestamp=order[12].isoformat(),
                        metadata={
                            'order_date': order[3].isoformat(),
                            'unit_price': float(order[5])
                        }
                    )
                    
                    # Send to Kafka
                    self.send_event('orders', asdict(order_event))
                    
                    # Update last processed timestamp
                    self.last_processed['orders'] = order[12]
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Error monitoring orders: {e}")
                
            time.sleep(5)  # Check every 5 seconds

    def monitor_inventory(self):
        """Monitor product inventory changes"""
        logger.info("Starting inventory monitoring...")
        
        # Simulate inventory monitoring (in real scenario, this would monitor actual inventory table)
        while self.running:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Get product data and simulate inventory changes
                cursor.execute("""
                SELECT product_id, product_name, cost_price, unit_price
                FROM products 
                WHERE is_active = true
                ORDER BY RANDOM()
                LIMIT 10
                """)
                
                products = cursor.fetchall()
                
                for product in products:
                    # Simulate inventory change
                    current_stock = max(0, int(time.time() % 100))  # Simulate stock level
                    previous_stock = current_stock + 5
                    reorder_point = 20
                    
                    # Determine event type
                    if current_stock < reorder_point:
                        event_type = 'low_stock_alert'
                    elif current_stock > previous_stock:
                        event_type = 'restock'
                    else:
                        event_type = 'stock_change'
                    
                    inventory_event = InventoryEvent(
                        product_id=product[0],
                        event_type=event_type,
                        current_stock=current_stock,
                        previous_stock=previous_stock,
                        reorder_point=reorder_point,
                        cost_per_unit=float(product[2]),
                        timestamp=datetime.now().isoformat(),
                        metadata={
                            'product_name': product[1],
                            'unit_price': float(product[3])
                        }
                    )
                    
                    self.send_event('inventory', asdict(inventory_event))
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Error monitoring inventory: {e}")
                
            time.sleep(10)  # Check every 10 seconds

    def monitor_prices(self):
        """Monitor price changes"""
        logger.info("Starting price monitoring...")
        
        while self.running:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Simulate price monitoring
                cursor.execute("""
                SELECT product_id, product_name, unit_price, cost_price
                FROM products 
                WHERE is_active = true
                ORDER BY RANDOM()
                LIMIT 5
                """)
                
                products = cursor.fetchall()
                
                for product in products:
                    # Simulate price change (20% chance)
                    if time.time() % 5 == 0:
                        old_price = float(product[2])
                        # Random price change ±10%
                        price_change = old_price * (0.9 + (time.time() % 0.2))
                        new_price = round(price_change, 2)
                        
                        if old_price != new_price:
                            discount_pct = ((old_price - new_price) / old_price) * 100
                            
                            price_event = PriceEvent(
                                product_id=product[0],
                                event_type='price_change',
                                old_price=old_price,
                                new_price=new_price,
                                discount_percentage=round(discount_pct, 2),
                                effective_date=datetime.now().isoformat(),
                                timestamp=datetime.now().isoformat(),
                                metadata={
                                    'product_name': product[1],
                                    'cost_price': float(product[3])
                                }
                            )
                            
                            self.send_event('prices', asdict(price_event))
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Error monitoring prices: {e}")
                
            time.sleep(15)  # Check every 15 seconds

    def simulate_customer_events(self):
        """Simulate customer behavior events"""
        logger.info("Starting customer event simulation...")
        
        while self.running:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Get random customers
                cursor.execute("""
                SELECT customer_id, customer_segment, email
                FROM customers 
                WHERE is_active = true
                ORDER BY RANDOM()
                LIMIT 3
                """)
                
                customers = cursor.fetchall()
                
                for customer in customers:
                    # Simulate different customer events
                    event_types = ['login', 'cart_action', 'profile_update', 'page_view']
                    event_type = event_types[int(time.time()) % len(event_types)]
                    
                    action_details = {
                        'login': {'device': 'mobile', 'location': 'USA'},
                        'cart_action': {'action': 'add_item', 'product_id': 123},
                        'profile_update': {'field': 'email', 'old_value': 'old@email.com'},
                        'page_view': {'page': 'product_detail', 'product_id': 456}
                    }
                    
                    customer_event = CustomerEvent(
                        customer_id=customer[0],
                        event_type=event_type,
                        customer_segment=customer[1],
                        action_details=action_details.get(event_type, {}),
                        timestamp=datetime.now().isoformat(),
                        metadata={
                            'email': customer[2]
                        }
                    )
                    
                    self.send_event('customers', asdict(customer_event))
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Error simulating customer events: {e}")
                
            time.sleep(8)  # Generate events every 8 seconds

    def _determine_order_event_type(self, order) -> str:
        """Determine event type based on order data"""
        created_at = order[11]
        updated_at = order[12]
        order_status = order[9]
        
        # If created and updated are very close, it's a new order
        if abs((updated_at - created_at).total_seconds()) < 60:
            return 'created'
        
        # Map status to event type
        status_map = {
            'PENDING': 'created',
            'CONFIRMED': 'confirmed',
            'SHIPPED': 'shipped',
            'DELIVERED': 'delivered',
            'CANCELLED': 'cancelled'
        }
        
        return status_map.get(order_status, 'updated')

    def start_monitoring(self):
        """Start all monitoring threads"""
        logger.info("Starting event producer monitoring...")
        
        # Create monitoring threads
        threads = [
            threading.Thread(target=self.monitor_orders, name='order_monitor'),
            threading.Thread(target=self.monitor_inventory, name='inventory_monitor'),
            threading.Thread(target=self.monitor_prices, name='price_monitor'),
            threading.Thread(target=self.simulate_customer_events, name='customer_events')
        ]
        
        # Start all threads
        for thread in threads:
            thread.daemon = True
            thread.start()
            logger.info(f"Started {thread.name}")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down event producer...")
        self.running = False
        
        if self.producer:
            self.producer.close()
            
        logger.info("Event producer stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start event producer
    producer = EventProducer()
    producer.start_monitoring()