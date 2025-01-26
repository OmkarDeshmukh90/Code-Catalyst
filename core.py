import pandas as pd
from sqlalchemy import create_engine
from joblib import load

class WasteAnalyzer:
    def __init__(self):
        # Initialize database connection
        self.engine = create_engine(
            "mysql+pymysql://root:abhi1234@localhost/food_demand_db"
        )
        
        # Load pre-trained models
        self.models = {
            'production': load('production_waste_predictor.joblib'),
            'retail': load('retail_anomaly_detector.joblib'),
            'consumption': load('consumption_clusterer.joblib')
        }

    def get_production_data(self):
        """Fetch and preprocess production data from database"""
        query = """
            SELECT date, crop_type, yield, storage_days, temperature, waste
            FROM production_data
        """
        df = pd.read_sql(query, self.engine)
        df['date'] = pd.to_datetime(df['date'])
        df['waste_percentage'] = df['waste'] / df['yield']
        return df

    def get_retail_data(self):
        """Fetch and preprocess retail data from database"""
        query = """
            SELECT store_id, product, stock_level, sales, discounts, waste, record_date
            FROM retail_data
        """
        df = pd.read_sql(query, self.engine)
        df['record_date'] = pd.to_datetime(df['record_date'])
        df['waste_ratio'] = df['waste'] / df['stock_level']
        return df

    def get_consumption_data(self):
        """Fetch and preprocess consumption data from database"""
        query = """
            SELECT household_id, meal_type, portion_size, leftovers, storage_method, record_date
            FROM consumption_data
        """
        df = pd.read_sql(query, self.engine)
        df['record_date'] = pd.to_datetime(df['record_date'])
        return df

    def predict_production_waste(self):
        """Generate production waste predictions"""
        df = self.get_production_data()
        features = df[['yield', 'storage_days', 'temperature']]
        df['predicted_waste'] = self.models['production'].predict(features)
        return df

    def detect_retail_anomalies(self):
        """Identify retail anomalies"""
        df = self.get_retail_data()
        features = df[['stock_level', 'sales', 'discounts', 'waste_ratio']]
        df['anomaly'] = self.models['retail'].predict(features)
        return df

    def analyze_consumption_patterns(self):
        """Cluster consumption patterns"""
        df = self.get_consumption_data()
        df['cluster'] = self.models['consumption'].predict(df)
        return df