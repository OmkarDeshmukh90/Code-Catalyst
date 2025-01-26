import pandas as pd
from sqlalchemy import create_engine, text
import random
from faker import Faker
from datetime import datetime, timedelta

# Database configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "abhi1234",
    "database": "food_demand_db"
}

# Create database connection
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

fake = Faker()

def create_tables():
    """Create tables for food waste analysis system"""
    tables = {
        'production_data': """
            CREATE TABLE IF NOT EXISTS production_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                crop_type VARCHAR(50) NOT NULL,
                yield DECIMAL(10,2) NOT NULL,
                storage_days INT NOT NULL,
                temperature DECIMAL(4,1) NOT NULL,
                waste DECIMAL(10,2) NOT NULL
            )
        """,
        'retail_data': """
            CREATE TABLE IF NOT EXISTS retail_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                store_id VARCHAR(10) NOT NULL,
                product VARCHAR(50) NOT NULL,
                stock_level INT NOT NULL,
                sales INT NOT NULL,
                discounts INT NOT NULL,
                waste DECIMAL(10,2) NOT NULL,
                record_date DATE NOT NULL
            )
        """,
        'consumption_data': """
            CREATE TABLE IF NOT EXISTS consumption_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                household_id VARCHAR(10) NOT NULL,
                meal_type VARCHAR(20) NOT NULL,
                portion_size INT NOT NULL,
                leftovers DECIMAL(4,1) NOT NULL,
                storage_method VARCHAR(20) NOT NULL,
                record_date DATE NOT NULL
            )
        """
    }

    with engine.connect() as conn:
        for table_name, ddl in tables.items():
            conn.execute(text(ddl))
            conn.commit()
    print("Tables created successfully")

def generate_production_data(num_records=100):
    """Generate sample production data"""
    crops = ['Tomatoes', 'Potatoes', 'Carrots', 'Onions', 'Cabbage']
    data = []
    
    for _ in range(num_records):
        record = {
            'date': fake.date_between(start_date='-1y', end_date='today'),
            'crop_type': random.choice(crops),
            'yield': round(random.uniform(500, 2000), 2),
            'storage_days': random.randint(1, 14),
            'temperature': round(random.uniform(2.0, 8.0), 1),
            'waste': 0  # Initialize waste
        }
        # Calculate waste as 5-15% of yield
        record['waste'] = round(record['yield'] * random.uniform(0.05, 0.15), 2)
        data.append(record)
    
    return pd.DataFrame(data)

def generate_retail_data(num_records=100):
    """Generate sample retail data"""
    products = ['Milk', 'Bread', 'Eggs', 'Cheese', 'Yogurt']
    data = []
    
    for _ in range(num_records):
        stock = random.randint(100, 500)
        sales = random.randint(80, stock - 20)
        discounts = random.randint(0, 10)
        
        record = {
            'store_id': fake.bothify(text='??###'),
            'product': random.choice(products),
            'stock_level': stock,
            'sales': sales,
            'discounts': discounts,
            'waste': stock - sales - discounts,
            'record_date': fake.date_between(start_date='-1y', end_date='today')
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_consumption_data(num_records=100):
    """Generate sample consumption data"""
    meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
    storage_methods = ['Refrigerated', 'Frozen', 'Pantry', 'Counter']
    
    data = []
    for _ in range(num_records):
        portion = random.randint(1, 6)
        record = {
            'household_id': fake.bothify(text='H####'),
            'meal_type': random.choice(meal_types),
            'portion_size': portion,
            'leftovers': round(random.uniform(0, portion * 0.3), 1),
            'storage_method': random.choice(storage_methods),
            'record_date': fake.date_between(start_date='-1y', end_date='today')
        }
        data.append(record)
    
    return pd.DataFrame(data)

def insert_sample_data():
    """Insert generated data into database"""
    tables = {
        'production_data': generate_production_data(),
        'retail_data': generate_retail_data(),
        'consumption_data': generate_consumption_data()
    }

    with engine.connect() as conn:
        for table_name, df in tables.items():
            # Check if table is empty
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            if result[0] == 0:
                df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists='append',
                    index=False
                )
                print(f"Inserted {len(df)} records into {table_name}")
            else:
                print(f"{table_name} already contains data - skipping insertion")
        conn.commit()

if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    print("Database setup complete")