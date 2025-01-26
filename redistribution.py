import pandas as pd
import numpy as np
from geopy.distance import geodesic
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
import json
import logging
from datetime import datetime, timedelta

# Database configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "abhi1234",
    "database": "food_demand_db"
}

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class RedistributionSystem:
    def __init__(self, max_distance_km: int = 50):
        self.engine = create_engine(
            f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
            f"@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}",
            pool_size=10,
            max_overflow=20
        )
        self.max_distance_km = max_distance_km
        self._verify_connection()

    def _verify_connection(self):
        """Verify database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logging.info("Database connection successful")
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            raise

    def get_surplus_items(self) -> pd.DataFrame:
        """Retrieve current surplus inventory with spatial data"""
        query = text("""
        SELECT i.item_id, 
               i.current_stock - r.required_stock AS surplus_quantity,
               i.category,
               s.latitude AS store_lat,
               s.longitude AS store_lon
        FROM Inventory i
        JOIN (
            SELECT item_id, 
                   daily_avg * days * (1 + buffer_stock) AS required_stock
            FROM InventoryStatus
            WHERE status = 'Surplus'
        ) r ON i.item_id = r.item_id
        JOIN Stores s ON i.location_id = s.store_id
        WHERE i.current_stock > r.required_stock
        """)
        
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logging.error(f"Error fetching surplus items: {str(e)}")
            return pd.DataFrame()

    def get_charities(self) -> pd.DataFrame:
        """Retrieve verified charities with capacity data"""
        query = text("""
        SELECT charity_id, name, latitude, longitude, 
               accepted_categories, operating_hours,
               capacity_kg - COALESCE(daily_used, 0) AS available_capacity
        FROM Charities c
        LEFT JOIN (
            SELECT charity_id, SUM(quantity) AS daily_used
            FROM RedistributionLogs
            WHERE DATE(scheduled_pickup) = CURDATE()
            GROUP BY charity_id
        ) r ON c.charity_id = r.charity_id
        WHERE verification_status = 'verified'
        """)
        
        try:
            charities = pd.read_sql(query, self.engine)
            charities['accepted_categories'] = charities['accepted_categories'].apply(
                lambda x: json.loads(x) if pd.notnull(x) else []
            )
            return charities
        except Exception as e:
            logging.error(f"Error fetching charities: {str(e)}")
            return pd.DataFrame()

    def _calculate_distances(self, origin: tuple, df: pd.DataFrame) -> pd.Series:
        """Vectorized distance calculation using NumPy"""
        earth_radius = 6371  # Earth radius in km
        lat1, lon1 = np.radians(origin[0]), np.radians(origin[1])
        lat2 = np.radians(df['latitude'].values)
        lon2 = np.radians(df['longitude'].values)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return earth_radius * c

    def _is_operating_now(self, operating_hours: str) -> bool:
        """Check if charity is currently operating"""
        try:
            hours = json.loads(operating_hours)
            now = datetime.now().time()
            current_weekday = datetime.now().weekday()
            
            time_slots = []
            if 'daily' in hours:
                time_slots.extend(hours['daily'].split(','))
            if current_weekday < 5 and 'weekdays' in hours:
                time_slots.extend(hours['weekdays'].split(','))
            if current_weekday >= 5 and 'weekends' in hours:
                time_slots.extend(hours['weekends'].split(','))
                
            for slot in time_slots:
                start_str, end_str = slot.split('-')
                start = datetime.strptime(start_str.strip(), "%H:%M").time()
                end = datetime.strptime(end_str.strip(), "%H:%M").time()
                if start <= now <= end:
                    return True
            return False
        except Exception as e:
            logging.warning(f"Error parsing operating hours: {str(e)}")
            return False

    def find_optimal_recipients(self, item_id: str, quantity: float, 
                              store_location: tuple) -> List[Dict]:
        """Find optimal recipients with capacity and timing constraints"""
        try:
            # Validate inputs
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
                
            # Get item categories
            query = text("SELECT category FROM Inventory WHERE item_id = :item_id")
            with self.engine.connect() as conn:
                result = conn.execute(query, {'item_id': item_id})
                categories = result.scalar()
            
            if not categories:
                raise ValueError(f"No categories found for item {item_id}")
                
            try:
                item_categories = json.loads(categories)
            except json.JSONDecodeError:
                item_categories = [c.strip() for c in categories.split(',')]

            # Get and filter charities
            charities = self.get_charities()
            if charities.empty:
                return []
                
            # Calculate distances
            charities['distance_km'] = self._calculate_distances(store_location, charities)
            charities = charities[charities['distance_km'] <= self.max_distance_km]
            
            # Filter by category and capacity
            mask = charities['accepted_categories'].apply(
                lambda x: any(cat in item_categories for cat in x)
            )
            suitable_charities = charities[mask & (charities['available_capacity'] > 0)]
            
            if suitable_charities.empty:
                return []
                
            # Prioritization
            suitable_charities = suitable_charities.sort_values(
                by=['available_capacity', 'distance_km'],
                ascending=[False, True]
            )
            
            # Allocate quantities
            allocations = []
            remaining = quantity
            
            for _, charity in suitable_charities.iterrows():
                alloc = min(remaining, charity['available_capacity'])
                allocations.append({
                    'charity_id': charity['charity_id'],
                    'charity_name': charity['name'],
                    'allocated_kg': alloc,
                    'distance_km': round(charity['distance_km'], 2),
                    'contact': f"{charity.get('contact_phone', '')} {charity.get('contact_email', '')}",
                    'operating_now': self._is_operating_now(charity['operating_hours'])
                })
                remaining -= alloc
                if remaining <= 0:
                    break
                    
            return allocations
            
        except Exception as e:
            logging.error(f"Redistribution error: {str(e)}", exc_info=True)
            return []

    def schedule_redistribution(self, allocations: List[Dict]) -> bool:
        """Bulk insert redistribution schedule"""
        if not allocations:
            return False
            
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                    INSERT INTO RedistributionLogs 
                    (item_id, charity_id, quantity, scheduled_pickup, status)
                    VALUES (:item_id, :charity_id, :allocated_kg, NOW(), 'scheduled')
                    """),
                    [{
                        'item_id': alloc['item_id'],
                        'charity_id': alloc['charity_id'],
                        'allocated_kg': alloc['allocated_kg']
                    } for alloc in allocations]
                )
            logging.info(f"Scheduled {len(allocations)} redistributions")
            return True
        except Exception as e:
            logging.error(f"Scheduling failed: {str(e)}")
            return False

    def full_redistribution_pipeline(self) -> Optional[pd.DataFrame]:
        """Automated pipeline with error handling"""
        try:
            surplus_df = self.get_surplus_items()
            if surplus_df.empty:
                logging.info("No surplus items found")
                return None
                
            all_allocations = []
            
            for _, item in surplus_df.iterrows():
                allocations = self.find_optimal_recipients(
                    item['item_id'],
                    item['surplus_quantity'],
                    (item['store_lat'], item['store_lon'])
                )
                
                if allocations:
                    for alloc in allocations:
                        alloc.update({
                            'item_id': item['item_id'],
                            'surplus_location': f"{item['store_lat']},{item['store_lon']}"
                        })
                    all_allocations.extend(allocations)
            
            if all_allocations:
                if self.schedule_redistribution(all_allocations):
                    return pd.DataFrame(all_allocations)
            return None
            
        except Exception as e:
            logging.error(f"Pipeline failed: {str(e)}", exc_info=True)
            return None

# Example usage
if __name__ == "__main__":
    rs = RedistributionSystem(max_distance_km=30)
    
    # Test single item allocation
    print("Testing single item allocation:")
    allocations = rs.find_optimal_recipients(
        "prod_0001",
        150,
        (19.0760, 72.8777)
    )
    print(pd.DataFrame(allocations))
    
    # Run full pipeline
    print("\nRunning full redistribution pipeline:")
    results = rs.full_redistribution_pipeline()
    if results is not None:
        print(results[['item_id', 'charity_name', 'allocated_kg', 'operating_now']])