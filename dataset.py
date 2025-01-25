import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -----------------------------
# 1. Generate Large Historical Sales Data (historical_sales.csv)
# -----------------------------

def generate_large_historical_sales_data():
    # Generate random dates over the last 5 years (2018-2023)
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # Food items for a larger selection
    food_items = [
        'Pizza', 'Burger', 'Pasta', 'Salad', 'Soup', 'Grilled Chicken',
        'BBQ Ribs', 'Fish and Chips', 'Fried Rice', 'Fruit Bowl', 'Ice Cream',
        'Lasagna', 'Noodles', 'Steak', 'Sushi', 'Tacos', 'Vegetable Stir Fry', 'Wraps', 'Quiche', 'Risotto'
    ]
    
    # Generate random demand data for each day and each food item
    data = []
    for date in dates:
        for food_item in food_items:
            demand = np.random.randint(50, 1000)  # Random demand between 50 and 1000 units
            data.append([date, food_item, demand])
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=['date', 'food_item', 'demand'])
    
    # Save to CSV
    df.to_csv('historical_sales_large.csv', index=False)
    print("Large Historical Sales Data saved to 'historical_sales_large.csv'.")

# -----------------------------
# 2. Generate Large Current Inventory Data (current_inventory.csv)
# -----------------------------

def generate_large_current_inventory_data():
    food_items = [
        'Pizza', 'Burger', 'Pasta', 'Salad', 'Soup', 'Grilled Chicken',
        'BBQ Ribs', 'Fish and Chips', 'Fried Rice', 'Fruit Bowl', 'Ice Cream',
        'Lasagna', 'Noodles', 'Steak', 'Sushi', 'Tacos', 'Vegetable Stir Fry', 'Wraps', 'Quiche', 'Risotto'
    ]
    
    inventory = [np.random.randint(50, 2000) for _ in food_items]  # Random inventory between 50 and 2000
    
    # Create DataFrame
    df = pd.DataFrame({
        'food_item': food_items,
        'current_supply': inventory
    })
    
    # Save to CSV
    df.to_csv('current_inventory_large.csv', index=False)
    print("Large Current Inventory Data saved to 'current_inventory_large.csv'.")

# -----------------------------
# 3. Generate Large Weather Data (temperature.csv)
# -----------------------------

def generate_large_weather_data():
    # Generate random temperature data for the entire range from 2018-2023
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Random temperature between 15°C to 35°C
    temperatures = np.random.randint(15, 35, size=len(dates))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'temperature': temperatures
    })
    
    # Save to CSV
    df.to_csv('temperature_large.csv', index=False)
    print("Large Weather Data saved to 'temperature_large.csv'.")

# -----------------------------
# 4. Generate Holiday Data (holidays.csv)
# -----------------------------

def generate_large_holiday_data():
    # Predefined major holidays (with additional holidays in the range)
    holiday_dates = pd.to_datetime([
        '2023-01-01', '2023-05-15', '2023-07-04', '2023-09-21', '2023-12-25',
        '2022-01-01', '2022-05-25', '2022-07-10', '2022-09-10', '2022-12-31',
        '2021-01-01', '2021-05-05', '2021-07-01', '2021-09-22', '2021-12-25',
        '2020-01-01', '2020-05-12', '2020-07-14', '2020-09-19', '2020-12-25',
        '2019-01-01', '2019-05-15', '2019-07-04', '2019-09-23', '2019-12-31'
    ])
    
    # Create DataFrame
    df = pd.DataFrame({
        'holiday_date': holiday_dates
    })
    
    # Save to CSV
    df.to_csv('holidays_large.csv', index=False)
    print("Holiday Data saved to 'holidays_large.csv'.")

# -----------------------------
# 5. Generate All Large Datasets
# -----------------------------

def generate_all_large_datasets():
    generate_large_historical_sales_data()
    generate_large_current_inventory_data()
    generate_large_weather_data()
    generate_large_holiday_data()

if __name__ == "__main__":
    generate_all_large_datasets()
    main
    
