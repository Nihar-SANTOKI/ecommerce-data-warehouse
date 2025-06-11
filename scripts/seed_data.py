#!/usr/bin/env python3
import os
import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta
import sys

fake = Faker()

def get_db_connection():
    """Create database connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def truncate_string(text, max_length):
    """Safely truncate string to max length"""
    if text and len(text) > max_length:
        return text[:max_length]
    return text

def seed_customers(conn, num_customers=1000):
    """Seed customers table with fake data"""
    cursor = conn.cursor()
    segments = ['PREMIUM', 'REGULAR', 'BASIC', 'VIP']
    
    print(f"Seeding {num_customers} customers...")
    
    for i in range(num_customers):
        try:
            # Generate phone number and truncate to 20 chars
            phone = fake.phone_number()
            phone = truncate_string(phone, 20)
            
            # Generate postal code and truncate to 20 chars
            postal_code = fake.zipcode()
            postal_code = truncate_string(postal_code, 20)
            
            # Truncate other fields that might be too long
            first_name = truncate_string(fake.first_name(), 50)
            last_name = truncate_string(fake.last_name(), 50)
            email = fake.unique.email()
            email = truncate_string(email, 100)  # Ensure email fits
            
            address = truncate_string(fake.street_address(), 100)
            city = truncate_string(fake.city(), 50)
            state = truncate_string(fake.state(), 50)
            
            cursor.execute("""
                INSERT INTO customers (
                    first_name, last_name, email, phone, address_line_1,
                    city, state, country, postal_code, registration_date,
                    customer_segment
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                first_name,
                last_name,
                email,
                phone,
                address,
                city,
                state,
                'USA',
                postal_code,
                fake.date_between(start_date='-2y', end_date='today'),
                random.choice(segments)
            ))
            
            # Commit every 100 records
            if (i + 1) % 100 == 0:
                conn.commit()
                print(f"  Inserted {i + 1} customers...")
                
        except Exception as e:
            print(f"Error inserting customer {i + 1}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print(f"Successfully seeded {num_customers} customers")

def seed_products(conn, num_products=500):
    """Seed products table with fake data"""
    cursor = conn.cursor()
    
    categories = [
        ('Electronics', ['Smartphones', 'Laptops', 'Tablets', 'Accessories']),
        ('Clothing', ['Men', 'Women', 'Kids', 'Accessories']),
        ('Home & Garden', ['Furniture', 'Decor', 'Kitchen', 'Garden']),
        ('Sports', ['Fitness', 'Outdoor', 'Team Sports', 'Water Sports']),
        ('Books', ['Fiction', 'Non-Fiction', 'Educational', 'Children'])
    ]
    
    brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE']
    suppliers = ['Supplier1', 'Supplier2', 'Supplier3', 'Supplier4']
    
    print(f"Seeding {num_products} products...")
    
    for i in range(num_products):
        try:
            category, subcategories = random.choice(categories)
            subcategory = random.choice(subcategories)
            
            # Generate realistic prices
            cost_price = round(random.uniform(10, 500), 2)
            unit_price = round(cost_price * random.uniform(1.2, 3.0), 2)
            
            # Generate product name and truncate to fit
            product_name = fake.bs().title()
            product_name = truncate_string(product_name, 200)
            
            # Truncate other fields
            brand = truncate_string(random.choice(brands), 50)
            supplier = truncate_string(random.choice(suppliers), 100)
            description = truncate_string(fake.text(max_nb_chars=200), 500)  # Assuming TEXT field
            
            cursor.execute("""
                INSERT INTO products (
                    product_name, category, subcategory, brand, supplier,
                    unit_price, cost_price, description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product_name,
                truncate_string(category, 50),
                truncate_string(subcategory, 50),
                brand,
                supplier,
                unit_price,
                cost_price,
                description
            ))
            
            # Commit every 100 records
            if (i + 1) % 100 == 0:
                conn.commit()
                print(f"  Inserted {i + 1} products...")
                
        except Exception as e:
            print(f"Error inserting product {i + 1}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print(f"Successfully seeded {num_products} products")

def seed_orders(conn, num_orders=5000):
    """Seed orders table with fake data"""
    cursor = conn.cursor()
    
    # Get customer and product IDs
    cursor.execute("SELECT customer_id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT product_id, unit_price FROM products")
    products = cursor.fetchall()
    
    if not customer_ids or not products:
        print("Error: No customers or products found. Please seed customers and products first.")
        return
    
    statuses = ['COMPLETED', 'SHIPPED', 'DELIVERED', 'PENDING', 'CANCELLED']
    payment_methods = ['CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'BANK_TRANSFER']
    
    print(f"Seeding {num_orders} orders...")
    
    for i in range(num_orders):
        try:
            customer_id = random.choice(customer_ids)
            product_id, unit_price = random.choice(products)
            quantity = random.randint(1, 5)
            
            # Random order date within last 2 years
            order_date = fake.date_time_between(start_date='-2y', end_date='now')
            
            # Calculate amounts
            gross_amount = float(unit_price) * quantity
            discount_amount = round(gross_amount * random.uniform(0, 0.2), 2)
            tax_amount = round(gross_amount * 0.08, 2)  # 8% tax
            total_amount = gross_amount - discount_amount + tax_amount
            
            # Truncate shipping address
            shipping_address = truncate_string(fake.address(), 500)  # Assuming TEXT field
            
            # Truncate status and payment method to fit VARCHAR constraints
            order_status = truncate_string(random.choice(statuses), 20)
            payment_method = truncate_string(random.choice(payment_methods), 20)
            
            cursor.execute("""
                INSERT INTO orders (
                    customer_id, product_id, order_date, quantity, unit_price,
                    discount_amount, tax_amount, total_amount, order_status,
                    payment_method, shipping_address
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                customer_id,
                product_id,
                order_date,
                quantity,
                unit_price,
                discount_amount,
                tax_amount,
                total_amount,
                order_status,
                payment_method,
                shipping_address
            ))
            
            # Commit every 200 records
            if (i + 1) % 200 == 0:
                conn.commit()
                print(f"  Inserted {i + 1} orders...")
                
        except Exception as e:
            print(f"Error inserting order {i + 1}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print(f"Successfully seeded {num_orders} orders")

def verify_data(conn):
    """Verify the seeded data"""
    cursor = conn.cursor()
    
    print("\nData verification:")
    tables = ['customers', 'products', 'orders']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count:,} records")
    
    # Show sample data
    print("\nSample data preview:")
    cursor.execute("""
        SELECT 
            c.first_name || ' ' || c.last_name as customer_name,
            p.product_name,
            o.total_amount,
            o.order_date::date
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON o.product_id = p.product_id
        ORDER BY o.order_date DESC
        LIMIT 5
    """)
    
    print("  Recent orders:")
    for row in cursor.fetchall():
        print(f"    {row[0]} bought {row[1]} for ${row[2]} on {row[3]}")

def main():
    """Main function to seed all data"""
    print("Starting data seeding process...")
    print("=" * 50)
    
    conn = get_db_connection()
    
    try:
        # Clear existing data (optional)
        print("Clearing existing data...")
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE orders CASCADE")
        cursor.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE customers RESTART IDENTITY CASCADE")
        conn.commit()
        print("Existing data cleared.\n")
        
        # Seed data in order (customers first, then products, then orders)
        seed_customers(conn, 1000)
        print()
        
        seed_products(conn, 500)
        print()
        
        seed_orders(conn, 5000)
        print()
        
        # Verify the data
        verify_data(conn)
        
        print("\n" + "=" * 50)
        print("✅ Data seeding completed successfully!")
        print("Your PostgreSQL database is now ready for dbt transformations.")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        conn.rollback()
        print("❌ Data seeding failed. Check the error above.")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()