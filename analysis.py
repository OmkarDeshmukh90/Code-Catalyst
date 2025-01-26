import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# Database configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "abhi1234",
    "database": "food_demand_db"
}

# Configuration constants
BUFFER_STOCK = 0.2  # 20% safety buffer
FORECAST_DAYS = [7, 15]  # Days to analyze for inventory

# Create database connection
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

def fetch_sales_data():
    """Retrieve historical sales data with product and weather information"""
    query = """
    SELECT 
        s.item_id,
        DATE(s.timestamp) AS sale_date,
        SUM(s.quantity) AS total_sold,
        AVG(w.temperature) AS avg_temp,
        AVG(w.precipitation) AS avg_precip
    FROM Sales s
    JOIN Weather w ON s.weather_id = w.weather_id
    JOIN Inventory i ON s.item_id = i.item_id
    GROUP BY s.item_id, DATE(s.timestamp)
    ORDER BY sale_date
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    return df

def prepare_forecast_data(item_df):
    """Format data for Prophet forecasting"""
    df = item_df[['sale_date', 'total_sold']].rename(columns={
        'sale_date': 'ds',
        'total_sold': 'y'
    })
    
    # Add external regressors
    df['avg_temp'] = item_df['avg_temp']
    df['avg_precip'] = item_df['avg_precip']
    
    return df

def generate_forecast(item_id, historical_data, periods=15):
    """Generate forecast using Prophet with weather factors"""
    try:
        # Initialize model
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        
        # Add weather regressors
        model.add_regressor('avg_temp')
        model.add_regressor('avg_precip')
        
        # Fit model
        model.fit(historical_data)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=periods)
        
        # Add weather forecast (replace with real weather data)
        future['avg_temp'] = historical_data['avg_temp'].mean()
        future['avg_precip'] = historical_data['avg_precip'].mean()
        
        # Generate forecast
        forecast = model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    except Exception as e:
        print(f"Error forecasting for {item_id}: {str(e)}")
        return None

def analyze_and_forecast():
    """Main forecasting workflow"""
    # Retrieve sales data
    sales_data = fetch_sales_data()
    
    # Get unique products
    products = sales_data['item_id'].unique()
    
    # Initialize results storage
    all_forecasts = []
    
    # Analyze and forecast for each product
    for product in products:  # Removed the [:10] limit
        product_data = sales_data[sales_data['item_id'] == product]
        
        if len(product_data) < 14:
            print(f"Skipping {product} - insufficient historical data")
            continue
            
        # Prepare data for forecasting
        prophet_data = prepare_forecast_data(product_data)
        
        # Generate 15-day forecast (includes 7-day)
        forecast = generate_forecast(product, prophet_data)
        
        if forecast is not None:
            # Add product ID to forecast
            forecast['item_id'] = product
            
            # Store results
            all_forecasts.append(forecast)
    
    # Combine all forecasts
    if all_forecasts:
        final_forecast = pd.concat(all_forecasts)
        final_forecast.to_csv('sales_forecasts.csv', index=False)
        print(f"Forecasts generated for {len(all_forecasts)} products")
        return final_forecast
    else:
        print("No forecasts generated")
        return None

def calculate_inventory_status(forecast_df, inventory_df):
    """Compare forecasts with inventory and identify surpluses/shortages"""
    # Handle items without sales data
    no_sales_items = inventory_df[~inventory_df['item_id'].isin(forecast_df['item_id'])]
    
    # Aggregate forecasts
    forecast_agg = forecast_df.groupby('item_id').agg({
        'yhat': ['sum', 'mean']
    }).reset_index()
    forecast_agg.columns = ['item_id', 'total_forecast', 'daily_avg']

    # Merge with inventory data using outer join
    merged_df = pd.merge(forecast_agg, inventory_df, on='item_id', how='right')
    
    # Fill NaN values for items without sales data
    merged_df['daily_avg'] = merged_df['daily_avg'].fillna(0)
    merged_df['total_forecast'] = merged_df['total_forecast'].fillna(0)
    
    # Calculate projected inventory for different periods
    results = []
    for days in FORECAST_DAYS:
        temp_df = merged_df.copy()
        temp_df['days'] = days
        temp_df['required_stock'] = temp_df['daily_avg'] * days * (1 + BUFFER_STOCK)
        temp_df['projected_inventory'] = temp_df['current_stock'] - temp_df['daily_avg'] * days
        temp_df['status'] = np.where(
            temp_df['current_stock'] > temp_df['required_stock'],
            'Surplus',
            np.where(
                temp_df['projected_inventory'] < 0,
                'Shortage',
                'Adequate'
            )
        )
        results.append(temp_df)
    
    return pd.concat(results)

def fetch_inventory_data():
    """Retrieve current inventory levels"""
    query = "SELECT item_id, current_stock FROM Inventory"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        inventory_df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return inventory_df

def calculate_inventory_status(forecast_df, inventory_df):
    """Compare forecasts with inventory and identify surpluses/shortages"""
    # Aggregate forecasts
    forecast_agg = forecast_df.groupby('item_id').agg({
        'yhat': ['sum', 'mean']
    }).reset_index()
    forecast_agg.columns = ['item_id', 'total_forecast', 'daily_avg']

    # Merge with inventory data
    merged_df = pd.merge(forecast_agg, inventory_df, on='item_id', how='right')
    
    # Calculate projected inventory for different periods
    results = []
    for days in FORECAST_DAYS:
        temp_df = merged_df.copy()
        temp_df['days'] = days
        temp_df['required_stock'] = temp_df['daily_avg'] * days * (1 + BUFFER_STOCK)
        temp_df['projected_inventory'] = temp_df['current_stock'] - temp_df['daily_avg'] * days
        temp_df['status'] = np.where(
            temp_df['current_stock'] > temp_df['required_stock'],
            'Surplus',
            np.where(
                temp_df['projected_inventory'] < 0,
                'Shortage',
                'Adequate'
            )
        )
        results.append(temp_df)
    
    return pd.concat(results)

def generate_recommendations(status_df):
    """Generate actionable recommendations based on inventory status"""
    recommendations = []
    
    for _, row in status_df.iterrows():
        item_id = row['item_id']
        current_stock = row['current_stock']
        required = row['required_stock']
        days = row['days']
        status = row['status']
        
        if status == 'Surplus':
            surplus = current_stock - required
            rec = {
                'item_id': item_id,
                'days': days,
                'type': 'Surplus',
                'amount': surplus,
                'recommendation': f"Redistribute {surplus:.0f} units or offer discounts"
            }
        elif status == 'Shortage':
            shortage = required - current_stock
            rec = {
                'item_id': item_id,
                'days': days,
                'type': 'Shortage',
                'amount': shortage,
                'recommendation': f"Order {shortage:.0f} units within {max(1, days-3)} days"
            }
        else:
            rec = {
                'item_id': item_id,
                'days': days,
                'type': 'Adequate',
                'amount': 0,
                'recommendation': "Maintain current stock levels"
            }
            
        recommendations.append(rec)
    
    return pd.DataFrame(recommendations)

def inventory_analysis(forecast_df):
    """Main inventory analysis workflow"""
    # Get current inventory
    inventory_df = fetch_inventory_data()
    
    # Calculate inventory status
    status_df = calculate_inventory_status(forecast_df, inventory_df)
    
    # Generate recommendations
    recommendations_df = generate_recommendations(status_df)
    
    # Save results
    status_df.to_csv('inventory_status.csv', index=False)
    recommendations_df.to_csv('inventory_recommendations.csv', index=False)
    
    # Print critical alerts
    critical_issues = recommendations_df[recommendations_df['type'] != 'Adequate']
    if not critical_issues.empty:
        print("\n🚨 Critical Inventory Alerts:")
        print(critical_issues[['item_id', 'days', 'type', 'recommendation']])
    else:
        print("\n✅ All inventory levels are adequate")
    
    return status_df, recommendations_df

def main():
    # Run analysis and forecasting
    forecast_df = analyze_and_forecast()
    
    if forecast_df is not None:
        # Perform inventory analysis
        status_df, recommendations_df = inventory_analysis(forecast_df)
        
        # Print summary
        print("\nInventory Status Summary:")
        print(status_df.groupby(['days', 'status']).size().unstack().fillna(0))
        
        print("\nTop Recommendations:")
        print(recommendations_df[recommendations_df['type'] != 'Adequate']
              .sort_values(['type', 'amount'], ascending=[True, False])
              .head(10))

if __name__ == "__main__":
    main()